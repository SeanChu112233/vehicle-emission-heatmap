import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import time

# 页面设置
st.set_page_config(
    page_title="车辆排放热图分析系统",
    page_icon="🚗",
    layout="wide"
)

# 进度指示器
def show_progress(step, total_steps, message):
    """显示处理进度"""
    progress = step / total_steps
    progress_bar = st.progress(progress)
    status_text = st.empty()
    status_text.text(f"🔄 {message}... ({step}/{total_steps})")
    return progress_bar, status_text

# 数据处理函数（带缓存）
@st.cache_data(show_spinner=False)
def load_and_process_data(uploaded_file):
    """加载和处理数据"""
    progress_bar, status_text = show_progress(1, 7, "读取Excel文件")
    
    # 读取Excel文件
    df = pd.read_excel(uploaded_file, header=1)
    
    status_text.text("🔄 重命名列... (2/7)")
    progress_bar.progress(2/7)
    # 重命名列
    df.columns = [
        '时间', 'Lambda', '催化器温度', 
        'CO原排', 'CO尾排', 
        'THC原排', 'THC尾排',
        'NOx原排', 'NOx尾排', '流量'
    ]
    
    status_text.text("🔄 处理缺失值... (3/7)")
    progress_bar.progress(3/7)
    # 处理缺失值和异常值
    df = df.fillna(0)
    for col in ['CO原排', 'CO尾排', 'THC原排', 'THC尾排', 'NOx原排', 'NOx尾排']:
        df[col] = df[col].clip(lower=0)
    
    status_text.text("🔄 数据采样... (4/7)")
    progress_bar.progress(4/7)
    # 数据采样（保持足够的数据点用于热图）
    df = df.iloc[::5, :].copy()  # 每5行取1行
    
    status_text.text("🔄 计算转化效率... (5/7)")
    progress_bar.progress(5/7)
    # 计算转化效率
    def calculate_efficiency(upstream, downstream):
        mask = (upstream > 0) & (downstream >= 0)
        result = np.zeros_like(upstream, dtype=float)
        result[mask] = (1 - downstream[mask] / upstream[mask]) * 100
        return np.clip(result, 0, 100)
    
    df['CO转化率'] = calculate_efficiency(df['CO原排'], df['CO尾排'])
    df['THC转化率'] = calculate_efficiency(df['THC原排'], df['THC尾排'])
    df['NOx转化率'] = calculate_efficiency(df['NOx原排'], df['NOx尾排'])
    
    status_text.text("🔄 创建热图数据... (6/7)")
    progress_bar.progress(6/7)
    # 创建热图数据
    heatmap_data = create_heatmap_data(df)
    
    status_text.text("✅ 数据处理完成... (7/7)")
    progress_bar.progress(1.0)
    time.sleep(0.5)
    progress_bar.empty()
    status_text.empty()
    
    return df, heatmap_data

def create_heatmap_data(df, bins=20):
    """创建热图所需的网格数据"""
    # 创建流量和温度的网格
    flow_bins = pd.cut(df['流量'], bins=bins)
    temp_bins = pd.cut(df['催化器温度'], bins=bins)
    
    # 计算每个网格的平均转化率
    heatmap_data = {}
    
    for pollutant in ['CO', 'THC', 'NOx']:
        # 分组计算平均值
        grouped = df.groupby([flow_bins, temp_bins])[f'{pollutant}转化率'].mean().unstack()
        
        # 获取网格中心值
        flow_centers = [interval.mid for interval in grouped.index.categories]
        temp_centers = [interval.mid for interval in grouped.columns.categories]
        
        # 填充NaN值
        z_data = grouped.fillna(0).values
        
        heatmap_data[pollutant] = {
            'flow_centers': flow_centers,
            'temp_centers': temp_centers,
            'efficiency_matrix': z_data
        }
    
    return heatmap_data

def create_2d_heatmap(heatmap_data, pollutant_name):
    """创建2D热图"""
    data = heatmap_data[pollutant_name]
    
    fig = go.Figure(data=go.Heatmap(
        z=data['efficiency_matrix'],
        x=data['flow_centers'],
        y=data['temp_centers'],
        colorscale='Viridis',
        colorbar=dict(
            title=dict(text="转化效率(%)", side="right"),
            thickness=15,
            len=0.8
        ),
        hoverongaps=False,
        hovertemplate=(
            '流量: %{x:.2f} m³/h<br>' +
            '温度: %{y:.2f} °C<br>' +
            '转化率: %{z:.2f}%<br>' +
            '<extra></extra>'
        )
    ))
    
    fig.update_layout(
        title=f"{pollutant_name}转化效率热图分析",
        xaxis_title='流量 (m³/h)',
        yaxis_title='催化器温度 (°C)',
        height=600,
        width=800
    )
    
    return fig

def create_contour_plot(heatmap_data, pollutant_name):
    """创建等高线图"""
    data = heatmap_data[pollutant_name]
    
    fig = go.Figure(data=go.Contour(
        z=data['efficiency_matrix'],
        x=data['flow_centers'],
        y=data['temp_centers'],
        colorscale='Viridis',
        contours=dict(
            coloring='heatmap',
            showlabels=True,
            labelfont=dict(size=12, color='white')
        ),
        colorbar=dict(
            title=dict(text="转化效率(%)", side="right"),
            thickness=15,
            len=0.8
        ),
        hoverongaps=False,
        hovertemplate=(
            '流量: %{x:.2f} m³/h<br>' +
            '温度: %{y:.2f} °C<br>' +
            '转化率: %{z:.2f}%<br>' +
            '<extra></extra>'
        )
    ))
    
    fig.update_layout(
        title=f"{pollutant_name}转化效率等高线图",
        xaxis_title='流量 (m³/h)',
        yaxis_title='催化器温度 (°C)',
        height=600,
        width=800
    )
    
    return fig

def create_combined_plot(heatmap_data, pollutant_name):
    """创建热图和散点图组合"""
    data = heatmap_data[pollutant_name]
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('热图', '等高线图'),
        specs=[[{"type": "heatmap"}, {"type": "contour"}]]
    )
    
    # 添加热图
    fig.add_trace(
        go.Heatmap(
            z=data['efficiency_matrix'],
            x=data['flow_centers'],
            y=data['temp_centers'],
            colorscale='Viridis',
            showscale=False,
            hovertemplate=(
                '流量: %{x:.2f}<br>温度: %{y:.2f}<br>效率: %{z:.2f}%<extra></extra>'
            )
        ),
        row=1, col=1
    )
    
    # 添加等高线图
    fig.add_trace(
        go.Contour(
            z=data['efficiency_matrix'],
            x=data['flow_centers'],
            y=data['temp_centers'],
            colorscale='Viridis',
            contours=dict(showlabels=True),
            showscale=False,
            hovertemplate=(
                '流量: %{x:.2f}<br>温度: %{y:.2f}<br>效率: %{z:.2f}%<extra></extra>'
            )
        ),
        row=1, col=2
    )
    
    fig.update_layout(
        title_text=f"{pollutant_name}转化效率分析",
        height=500,
        width=1000,
        coloraxis=dict(colorscale='Viridis')
    )
    
    fig.update_xaxes(title_text="流量 (m³/h)", row=1, col=1)
    fig.update_yaxes(title_text="催化器温度 (°C)", row=1, col=1)
    fig.update_xaxes(title_text="流量 (m³/h)", row=1, col=2)
    fig.update_yaxes(title_text="催化器温度 (°C)", row=1, col=2)
    
    return fig

# 显示统计信息
def show_statistics(df):
    """显示数据统计信息"""
    st.subheader("📊 数据统计信息")
    
    cols = st.columns(4)
    metrics = [
        ("总数据点数", f"{len(df):,}"),
        ("CO平均转化率", f"{df['CO转化率'].mean():.1f}%"),
        ("THC平均转化率", f"{df['THC转化率'].mean():.1f}%"), 
        ("NOx平均转化率", f"{df['NOx转化率'].mean():.1f}%")
    ]
    
    for col, (label, value) in zip(cols, metrics):
        with col:
            st.metric(label, value)
    
    # 显示数据分布
    with st.expander("📋 查看数据分布详情"):
        st.dataframe(df[['流量', '催化器温度', 'CO转化率', 'THC转化率', 'NOx转化率']].describe())

# 主程序
def main():
    st.title("🚗 车辆排放热图分析系统")
    st.markdown("""
    ### 📈 基于2D热图的转化效率分析
    通过热图可视化流量、温度与污染物转化率之间的关系，性能更优且更直观。
    """)
    
    # 文件上传
    uploaded_file = st.file_uploader(
        "上传Excel数据文件", 
        type=["xlsx", "xls"],
        help="支持.xlsx和.xls格式，请确保文件格式正确"
    )
    
    if uploaded_file:
        try:
            # 加载和处理数据
            df, heatmap_data = load_and_process_data(uploaded_file)
            
            # 显示数据预览
            with st.expander("📋 数据预览", expanded=False):
                st.dataframe(df.head(10), use_container_width=True)
                st.info(f"原始数据: {len(df)} 行 × {len(df.columns)} 列")
            
            # 显示统计信息
            show_statistics(df)
            
            # 可视化选项
            st.subheader("📊 可视化分析")
            visualization_type = st.radio(
                "选择可视化类型:",
                ["热图", "等高线图", "组合视图"],
                horizontal=True
            )
            
            # 污染物选择
            pollutant = st.selectbox(
                "选择污染物:",
                ["CO", "THC", "NOx"]
            )
            
            # 生成图表
            if visualization_type == "热图":
                fig = create_2d_heatmap(heatmap_data, pollutant)
            elif visualization_type == "等高线图":
                fig = create_contour_plot(heatmap_data, pollutant)
            else:
                fig = create_combined_plot(heatmap_data, pollutant)
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 同时显示三个污染物的热图
            st.subheader("📊 三种污染物对比")
            cols = st.columns(3)
            pollutants = ["CO", "THC", "NOx"]
            
            for col, poll in zip(cols, pollutants):
                with col:
                    small_fig = create_2d_heatmap(heatmap_data, poll)
                    small_fig.update_layout(height=400, width=350, title=f"{poll}转化率")
                    st.plotly_chart(small_fig, use_container_width=True)
            
            # 添加数据下载功能
            st.subheader("💾 数据导出")
            csv = df.to_csv(index=False)
            st.download_button(
                label="下载处理后的CSV数据",
                data=csv,
                file_name="排放分析结果.csv",
                mime="text/csv"
            )
            
            # 使用说明
            with st.expander("ℹ️ 使用说明"):
                st.markdown("""
                - **热图颜色**: 深蓝色→绿色→黄色→红色表示效率从低到高
                - **数据采样**: 10Hz数据降采样到2Hz以保证性能
                - **网格统计**: 每个网格显示该区域内数据的平均转化率
                - **交互操作**: 鼠标悬停查看详细数据，点击图例可筛选
                """)
                
        except Exception as e:
            st.error(f"❌ 数据处理错误: {str(e)}")
            st.exception(e)
    else:
        st.info("👆 请上传Excel文件开始分析")

if __name__ == "__main__":
    main()
