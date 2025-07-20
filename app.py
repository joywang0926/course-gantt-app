import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide")
st.title("📅 課程甘特圖與衝堂檢測系統")

# 載入課程資料
@st.cache_data
def load_data():
    df = pd.read_excel("courses.xlsx")
    df['勾選'] = True
    return df

df = load_data()

# 課程資訊表格 (上方)
st.subheader("📋 課程資訊（請勾選要顯示的課程）")
edited_df = st.data_editor(
    df,
    column_config={
        "勾選": st.column_config.CheckboxColumn(
            "選取課程", help="勾選以顯示課程", default=True
        )
    },
    hide_index=True,
    use_container_width=True,
    height=250
)

selected_courses = edited_df[edited_df["勾選"]]

# 衝堂偵測
schedule, conflict_ranges = {}, {}
for _, row in selected_courses.iterrows():
    day, course = row["星期"], row["課程名稱"]
    start_wk, end_wk = map(int, row["週次"].split("-"))
    for wk in range(start_wk, end_wk + 1):
        key = (day, wk)
        if key in schedule:
            existing_course = schedule[key]
            pair = tuple(sorted([existing_course, course]))
            conflict_ranges[pair] = conflict_ranges.get(pair, set())
            conflict_ranges[pair].add((day, wk))
        else:
            schedule[key] = course

# 下方左右分區：甘特圖（左側）與衝堂資訊（右側）
gantt_col, conflict_col = st.columns([2, 1])

# 左側甘特圖
with gantt_col:
    days_order = ["一", "二", "三", "四", "五", "六"]
    days_order_reverse = days_order[::-1]
    days_mapping = {day: idx for idx, day in enumerate(days_order_reverse)}

    gantt_display = {}
    for _, row in selected_courses.iterrows():
        day = row["星期"]
        if day not in gantt_display:
            gantt_display[day] = {
                '課程': row["課程名稱"],
                'Start': int(row["週次"].split("-")[0]),
                'Finish': int(row["週次"].split("-")[1]),
                'Color': row["顏色(RGB)"]
            }

    fig = go.Figure()
    for day, task in gantt_display.items():
        fig.add_trace(go.Bar(
            x=[task["Finish"] - task["Start"] + 1],
            y=[days_mapping[day]],
            base=task["Start"],
            orientation='h',
            marker=dict(color=task["Color"]),
            text=task["課程"],
            textposition='inside',
            insidetextanchor='middle',
            hovertemplate=f"{task['課程']} 第{task['Start']}-{task['Finish']}週<extra></extra>",
            showlegend=False,
            textfont=dict(size=14, color="black"),
        ))

    # 衝堂紅框標示
    for (course1, course2), conflicts in conflict_ranges.items():
        days = {day for day, _ in conflicts}
        for day in days:
            wks = sorted(wk for d, wk in conflicts if d == day)
            fig.add_shape(
                type="rect",
                x0=min(wks)-0.1, x1=max(wks)+0.9,
                y0=days_mapping[day]-0.4,
                y1=days_mapping[day]+0.4,
                line=dict(color="red", width=3),
                fillcolor='rgba(0,0,0,0)',
                layer='above'
            )

    fig.update_xaxes(
        range=[0.5, 18.5],
        tickvals=list(range(1, 19)),
        title="週次"
    )

    fig.update_yaxes(
        tickvals=list(range(len(days_order))),
        ticktext=days_order_reverse,
        title="星期"
    )

    fig.update_layout(
        height=500,
        margin=dict(l=100, r=20, t=50, b=50),
        plot_bgcolor='rgba(240,240,245,1)',
        paper_bgcolor='rgba(255,255,255,1)',
        title="📚 課程甘特圖"
    )

    st.plotly_chart(fig, use_container_width=True)

# 右側衝堂資訊
with conflict_col:
    st.subheader("⚠️ 衝堂資訊")
    if conflict_ranges:
        for (course1, course2), conflicts in conflict_ranges.items():
            days = {day for day, _ in conflicts}
            for day in days:
                weeks = sorted(wk for d, wk in conflicts if d == day)
                st.error(f"【{course1}】與【{course2}】"
                         f" 星期{day} 第{weeks[0]}-{weeks[-1]}週衝堂。")
    else:
        st.success("✅ 目前選課無衝堂！")
