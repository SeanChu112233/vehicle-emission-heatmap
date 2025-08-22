import streamlit as st
import pandas as pd
import numpy as np

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
            conversion = (original - tail) / original * 100
            conversion = np.where(conversion < 0, 0, conversion)
            conversion = np.where(conversion > 100, 100, conversion)
            return conversion
        
        # 计算各污染物的转化效率
        df['CO转化效率'] = calculate_conversion(df['CO原排'], df['CO尾排'])
        df['THC转化效率'] = calculate_conversion(df['THC原排'], df['THC尾排'])
        df['NOx转化效率'] = calculate_conversion(df['NOx原排'], df['NOx尾排'])
        
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
        
        # 添加下载处理后的数据功能
        st.subheader("下载处理后的数据")
        csv = df.to_csv(index=False)
        st.download_button(
            label="下载CSV格式数据",
            data=csv,
            file_name="处理后的排放数据.csv",
            mime="text/csv"
        )
        
    except Exception as e:
        st.error(f"处理数据时发生错误: {str(e)}")
else:
    st.info("请上传CSV数据文件以开始分析。")
