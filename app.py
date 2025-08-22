import streamlit as st
import pandas as pd
import numpy as np
import base64
import io

# 设置页面标题
st.set_page_config(page_title="排放数据分析", layout="wide")
st.title("车辆排放数据可视化分析")

# 文件上传
uploaded_file = st.file_uploader("上传CSV数据文件", type=["csv"])

if uploaded_file is not None:
    try:
        # 读取CSV数据
        df = pd.read_csv(uploaded_file)
        
        # 显示数据基本信息
        st.subheader("数据概览")
        st.write(f"数据总行数: {len(df)}")
        st.write("前5行数据:")
        st.dataframe(df.head())
        
        # 计算转化效率函数
        def calculate_conversion(original, tail):
            # 避免除以零错误
            conversion = np.zeros_like(original, dtype=float)
            mask = original > 0
            conversion[mask] = (original[mask] - tail[mask]) / original[mask] * 100
            conversion = np.where(conversion < 0, 0, conversion)
            conversion = np.where(conversion > 100, 100, conversion)
            return conversion
        
        # 计算各污染物的转化效率
        df['CO转化效率'] = calculate_conversion(df['CO原排'], df['CO尾排'])
        df['THC转化效率'] = calculate_conversion(df['THC原排'], df['THC尾排'])
        df['NOx转化效率'] = calculate_conversion(df['NOx原排'], df['NOx尾排'])
        
        # 显示统计数据
        st.subheader("转化效率统计")
        stats_data = {
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
        }
        
        # 创建简单的表格显示
        st.write("| 污染物 | 平均转化效率 (%) | 最小转化效率 (%) | 最大转化效率 (%) |")
        st.write("|--------|------------------|------------------|------------------|")
        for i in range(3):
            st.write(f"| {stats_data['污染物'][i]} | {stats_data['平均转化效率 (%)'][i]:.2f} | {stats_data['最小转化效率 (%)'][i]:.2f} | {stats_data['最大转化效率 (%)'][i]:.2f} |")
        
        # 添加下载处理后的数据功能
        st.subheader("下载处理后的数据")
        csv = df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="处理后的排放数据.csv">下载CSV格式数据</a>'
        st.markdown(href, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"处理数据时发生错误: {str(e)}")
        st.error("请确保CSV文件格式正确，包含所有必需的列")
else:
    st.info("请上传CSV数据文件以开始分析。")

# 添加使用说明
with st.expander("使用说明"):
    st.markdown("""
    1. 请先将Excel文件转换为CSV格式
    2. CSV文件应包含以下列：时间, Lambda, 催化器温度, CO原排, CO尾排, THC原排, THC尾排, NOx原排, NOx尾排, 流量
    3. 系统将自动计算三种污染物(CO, THC, NOx)的转化效率
    4. 转化效率计算公式：(原排 - 尾排) / 原排 × 100%
    5. 转化效率限制在0-100%范围内
    """)
