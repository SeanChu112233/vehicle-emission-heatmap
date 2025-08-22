import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io

# 设置页面标题
st.set_page_config(page_title="排放数据分析", layout="wide")
st.title("车辆排放数据可视化分析")

# 文件上传
uploaded_file = st.file_uploader("上传Excel数据文件", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        # 读取数据，跳过第一行空白行，第二行作为列名
        df = pd.read_excel(uploaded_file, skiprows=[0], header=0)
        
        # 重命名列
        df.columns = ['时间', 'Lambda', '催化器温度', 'CO原排', 'CO尾排', 
                     'THC原排', 'THC尾排', 'NOx原排', 'NOx尾排', '流量']
        
        # 显示数据基本信息
        st.subheader("数据概览")
        st.write(f"数据总行数: {len(df)}")
        st.write("前5行数据:")
        st.dataframe(df.head())
        
        # 计算转化效率函数
        def calculate_conversion(original, tail):
            conversion = (original - tail) / original * 100
            conversion = np.where(conversion < 0, 0, conversion)
            conversion = np.where(conversion > 100, 100, conversion)
            return conversion
        
        # 计算各污染物的转化效率
        df['CO转化效率'] = calculate_conversion(df['CO原排'], df['CO尾排'])
        df['THC转化效率'] = calculate_conversion(df['THC原排'], df['THC尾排'])
        df['NOx转化效率'] = calculate_conversion(df['NOx原排'], df['NOx尾排'])
        
        # 创建自定义颜色映射
        colors = [(0, 0, 0.5),   # 深蓝色 (0%)
                  (0, 0.5, 1),   # 蓝色 (25%)
                  (0, 1, 0),     # 绿色 (50%)
                  (1, 0.8, 0),   # 橘红色 (70%)
                  (1, 0, 0)]     # 深红色 (90-100%)
        
        positions = [0, 0.25, 0.5, 0.7, 1.0]
        
        # 创建三个污染物的图表
        st.subheader("污染物转化效率分析")
        
        # 使用Plotly创建散点图而不是插值图，避免scipy依赖
        pollutants = ['CO', 'THC', 'NOx']
        efficiency_cols = ['CO转化效率', 'THC转化效率', 'NOx转化效率']
        
        for i, (pollutant, eff_col) in enumerate(zip(pollutants, efficiency_cols)):
            fig = go.Figure(data=go.Scatter(
                x=df['流量'],
                y=df['催化器温度'],
                mode='markers',
                marker=dict(
                    size=5,
                    color=df[eff_col],
                    colorscale=[
                        [0, 'rgb(0, 0, 127)'],     # 深蓝色
                        [0.25, 'rgb(0, 0, 255)'],  # 蓝色
                        [0.5, 'rgb(0, 255, 0)'],   # 绿色
                        [0.7, 'rgb(255, 165, 0)'], # 橘红色
                        [1.0, 'rgb(255, 0, 0)']    # 深红色
                    ],
                    colorbar=dict(
                        title=f"{pollutant}转化效率 (%)",
                        titleside='right'
                    ),
                    cmin=0,
                    cmax=100,
                    showscale=True
                ),
                hovertemplate=
                '<b>流量</b>: %{x:.2f}<br>' +
                '<b>温度</b>: %{y:.2f}<br>' +
                '<b>转化效率</b>: %{marker.color:.2f}%<br>' +
                '<extra></extra>'
            ))
            
            fig.update_layout(
                title=f"{pollutant}转化效率",
                xaxis_title="流量",
                yaxis_title="催化器温度",
                width=800,
                height=600
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # 显示统计数据
        st.subheader("转化效率统计")
        stats_df = pd.DataFrame({
            '污染物': ['CO', 'THC', 'NOx'],
            '平均转化效率 (%)': [
                df['CO转化效率'].mean(),
                df['THC转化效率'].mean(),
                df['NOx转化效率'].mean()
            ],
            '最小转化效率 (%)': [
                df['CO转化效率'].min(),
                df['THC转化效率'].min(),
                df['NOx转化效率'].min()
            ],
            '最大转化效率 (%)': [
                df['CO转化效率'].max(),
                df['THC转化效率'].max(),
                df['NOx转化效率'].max()
            ]
        })
        st.dataframe(stats_df)
        
    except Exception as e:
        st.error(f"处理数据时发生错误: {str(e)}")
        st.error("请确保Excel文件格式正确：第一行为空白，第二行为列名，数据从第三行开始")
else:
    st.info("请上传Excel数据文件以开始分析。")

# 添加使用说明
with st.expander("使用说明"):
    st.markdown("""
    1. 上传Excel数据文件，文件格式应符合以下要求：
       - 第一行为空白行
       - 第二行为列名：时间, Lambda, 催化器温度, CO原排, CO尾排, THC原排, THC尾排, NOx原排, NOx尾排, 流量
       - 数据从第三行开始
    2. 系统将自动计算三种污染物(CO, THC, NOx)的转化效率
    3. 转化效率计算公式：(原排 - 尾排) / 原排 × 100%
    4. 转化效率限制在0-100%范围内
    5. 图表使用散点图显示数据点，颜色表示转化效率
    """)
