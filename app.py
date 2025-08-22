import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from scipy.interpolate import griddata
import plotly.graph_objects as go

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
        custom_cmap = LinearSegmentedColormap.from_list("custom_cmap", list(zip(positions, colors)))
        
        # 创建插值网格
        def create_interpolated_plot(x, y, z, title, x_label, y_label, z_label):
            # 创建网格
            xi = np.linspace(x.min(), x.max(), 500)
            yi = np.linspace(y.min(), y.max(), 500)
            xi, yi = np.meshgrid(xi, yi)
            
            # 插值
            zi = griddata((x, y), z, (xi, yi), method='linear')
            
            # 创建图形
            fig = go.Figure(data=
                go.Contour(
                    x=xi[0], 
                    y=yi[:,0], 
                    z=zi,
                    colorscale=[
                        [0, 'rgb(0, 0, 127)'],     # 深蓝色
                        [0.25, 'rgb(0, 0, 255)'],  # 蓝色
                        [0.5, 'rgb(0, 255, 0)'],   # 绿色
                        [0.7, 'rgb(255, 165, 0)'], # 橘红色
                        [1.0, 'rgb(255, 0, 0)']    # 深红色
                    ],
                    colorbar=dict(
                        title=z_label,
                        titleside='right'
                    ),
                    contours=dict(
                        start=0,
                        end=100,
                        size=10
                    ),
                    hovertemplate=
                    '<b>流量</b>: %{x:.2f}<br>' +
                    '<b>温度</b>: %{y:.2f}<br>' +
                    '<b>转化效率</b>: %{z:.2f}%<br>' +
                    '<extra></extra>'
                )
            )
            
            fig.update_layout(
                title=title,
                xaxis_title=x_label,
                yaxis_title=y_label,
                width=800,
                height=600
            )
            
            return fig
        
        # 创建三个污染物的图表
        st.subheader("污染物转化效率分析")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.plotly_chart(create_interpolated_plot(
                df['流量'], df['催化器温度'], df['CO转化效率'],
                "CO转化效率", "流量", "催化器温度", "CO转化效率 (%)"
            ), use_container_width=True)
        
        with col2:
            st.plotly_chart(create_interpolated_plot(
                df['流量'], df['催化器温度'], df['THC转化效率'],
                "THC转化效率", "流量", "催化器温度", "THC转化效率 (%)"
            ), use_container_width=True)
        
        with col3:
            st.plotly_chart(create_interpolated_plot(
                df['流量'], df['催化器温度'], df['NOx转化效率'],
                "NOx转化效率", "流量", "催化器温度", "NOx转化效率 (%)"
            ), use_container_width=True)
        
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
    5. 图表使用插值法填充缺失数据，形成连续表面
    """)
