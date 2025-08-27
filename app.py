import streamlit as st
import pandas as pd
import numpy as np
import base64
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import io

# 设置页面标题
st.set_page_config(page_title="排放数据分析", layout="wide")
st.title("车辆排放数据可视化分析")

# 显示CSV格式要求
with st.expander("CSV文件格式要求", expanded=True):
    st.markdown("""
    ### CSV文件应包含以下列（按顺序）：
    1. 时间
    2. Lambda
    3. 催化器温度
    4. CO原排
    5. CO尾排
    6. THC原排
    7. THC尾排
    8. NOx原排
    9. NOx尾排
    10. 流量
    
    ### 将Excel转换为CSV的方法：
    1. 打开Excel文件
    2. 点击"文件" → "另存为"
    3. 选择保存类型为"CSV (逗号分隔)(*.csv)"
    4. 点击保存
    
    ### 注意事项：
    - 确保第一行是列标题（不需要空白行）
    - 确保数据从第二行开始
    - 确保列的顺序与上述一致
    """)

# 文件上传
uploaded_file = st.file_uploader("上传CSV数据文件", type=["csv"])

if uploaded_file is not None:
    try:
        # 读取CSV数据
        df = pd.read_csv(uploaded_file)
        
        # 检查必需的列是否存在
        required_columns = ['时间', 'Lambda', '催化器温度', 'CO原排', 'CO尾排', 
                           'THC原排', 'THC尾排', 'NOx原排', 'NOx尾排', '流量']
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            st.error(f"CSV文件缺少以下必需的列: {', '.join(missing_columns)}")
            st.info("请确保CSV文件包含所有必需的列，并且列名正确")
        else:
            # 显示数据基本信息
            st.subheader("数据概览")
            st.write(f"数据总行数: {len(df)}")
            
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
            df['CO Conv'] = calculate_conversion(df['CO原排'], df['CO尾排'])
            df['THC Conv'] = calculate_conversion(df['THC原排'], df['THC尾排'])
            df['NOx Conv'] = calculate_conversion(df['NOx原排'], df['NOx尾排'])
            
            # 创建自定义颜色映射
            colors = [
                (0, 0, 0.5),    # 深蓝色 (0%)
                (0, 0, 1),      # 蓝色 (25%)
                (0, 1, 0),      # 绿色 (50%)
                (1, 0.65, 0),   # 橘红色 (70%)
                (1, 0, 0)       # 深红色 (90-100%)
            ]
            positions = [0, 0.25, 0.5, 0.7, 1.0]
            custom_cmap = LinearSegmentedColormap.from_list("custom_cmap", list(zip(positions, colors)))
            
            # 创建三个污染物的热点图
            st.subheader("污染物转化效率热点图")
            
            pollutants = ['CO', 'THC', 'NOx']
            efficiency_cols = ['CO Conv', 'THC Conv', 'NOx Conv']
            
            for pollutant, eff_col in zip(pollutants, efficiency_cols):
                st.write(f"### {pollutant}转化效率热点图")
                
                # 创建图表
                fig, ax = plt.subplots(figsize=(10, 6))
                scatter = ax.scatter(
                    df['流量'], 
                    df['催化器温度'], 
                    c=df[eff_col], 
                    cmap=custom_cmap, 
                    vmin=0, 
                    vmax=100,
                    alpha=0.7
                )
                
                # 设置图表属性
                ax.set_xlabel('流量')
                ax.set_ylabel('催化器温度')
                ax.set_title(f'{pollutant}转化效率热点图')
                
                # 添加颜色条
                cbar = plt.colorbar(scatter)
                cbar.set_label('Conversion (%)')
                
                # 显示图表
                st.pyplot(fig)
                plt.close(fig)
            
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
    2. CSV文件应包含以下列（按顺序）：
       - 时间
       - Lambda
       - 催化器温度
       - CO原排
       - CO尾排
       - THC原排
       - THC尾排
       - NOx原排
       - NOx尾排
       - 流量
    3. 系统将自动计算三种污染物(CO, THC, NOx)的转化效率
    4. 转化效率计算公式：(原排 - 尾排) / 原排 × 100%
    5. 转化效率限制在0-100%范围内
    6. 图表使用散点图显示数据点，颜色表示转化效率
    7. 颜色映射：
       - 0%: 深蓝色
       - 25%: 蓝色
       - 50%: 绿色
       - 70%: 橘红色
       - 90-100%: 深红色
    """)
