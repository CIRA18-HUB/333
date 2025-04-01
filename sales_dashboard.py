import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import re
import os

# 设置页面配置
st.set_page_config(
    page_title="销售数据分析仪表盘",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 定义一些更美观的自定义CSS样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.8rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 2rem;
        padding: 1.5rem;
        background-color: #f8f9fa;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        letter-spacing: 0.05em;
    }
    .sub-header {
        font-size: 1.8rem;
        color: #0D47A1;
        padding-top: 1.5rem;
        padding-bottom: 1rem;
        margin-top: 1rem;
        border-bottom: 2px solid #E3F2FD;
        letter-spacing: 0.04em;
    }
    .card {
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        background-color: white;
        transition: transform 0.3s;
    }
    .card:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: bold;
        color: #1E88E5;
        margin: 0.5rem 0;
        letter-spacing: 0.05em;
        line-height: 1.3;
    }
    .metric-label {
        font-size: 1.1rem;
        color: #424242;
        font-weight: 500;
        letter-spacing: 0.03em;
        margin-bottom: 0.3rem;
    }
    .highlight {
        background-color: #E3F2FD;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1.5rem 0;
        border-left: 5px solid #1E88E5;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        border-radius: 5px 5px 0 0;
        letter-spacing: 0.03em;
    }
    .stTabs [aria-selected="true"] {
        background-color: #E3F2FD;
        border-bottom: 3px solid #1E88E5;
    }
    .stExpander {
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    .download-button {
        text-align: center;
        margin-top: 2rem;
    }
    .section-gap {
        margin-top: 2.5rem;
        margin-bottom: 2.5rem;
    }
    /* 调整图表容器的样式 */
    .st-emotion-cache-1wrcr25 {
        margin-top: 2rem !important;
        margin-bottom: 3rem !important;
        padding: 1rem !important;
    }
    /* 设置侧边栏样式 */
    .st-emotion-cache-6qob1r {
        background-color: #f5f7fa;
        border-right: 1px solid #e0e0e0;
    }
    [data-testid="stSidebar"]{
        background-color: #f8f9fa;
    }
    [data-testid="stSidebarNav"]{
        padding-top: 2rem;
    }
    .sidebar-header {
        font-size: 1.3rem;
        color: #0D47A1;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #e0e0e0;
        letter-spacing: 0.03em;
    }
    /* 调整图表字体大小 */
    .js-plotly-plot .plotly .ytick text,
    .js-plotly-plot .plotly .xtick text {
        font-size: 14px !important;
        letter-spacing: 0.02em !important;
    }
    .js-plotly-plot .plotly .gtitle {
        font-size: 18px !important;
        letter-spacing: 0.03em !important;
    }
    /* 图表标签间距 */
    .js-plotly-plot .plotly text {
        letter-spacing: 0.02em !important;
    }
</style>
""", unsafe_allow_html=True)

# 标题
st.markdown('<div class="main-header">销售数据分析仪表盘</div>', unsafe_allow_html=True)


# 格式化数值的函数
def format_yuan(value):
    if value >= 100000000:  # 亿元级别
        return f"{value / 100000000:.2f}亿元"
    elif value >= 10000:  # 万元级别
        return f"{value / 10000:.2f}万元"
    else:
        return f"{value:.2f}元"


# 加载数据函数 - 修复版本
@st.cache_data
def load_data(file_path=None):
    """
    从文件加载数据或使用示例数据，增强错误处理
    """
    # 如果提供了文件路径，从文件加载
    if file_path and os.path.exists(file_path):
        try:
            df = pd.read_excel(file_path)

            # 数据预处理
            # 确保所有必要的列都存在
            required_columns = ['客户简称', '所属区域', '发运月份', '申请人', '产品代码', '产品名称',
                                '订单类型', '单价（箱）', '数量（箱）']

            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                st.error(f"文件缺少必要的列: {', '.join(missing_columns)}。使用示例数据进行演示。")
                return load_sample_data()

            # 计算销售额
            df['销售额'] = df['单价（箱）'] * df['数量（箱）']

            # 确保发运月份是日期类型
            try:
                df['发运月份'] = pd.to_datetime(df['发运月份'])
            except Exception as e:
                st.warning(f"转换日期格式时出错: {str(e)}。月份分析功能可能受影响。")

            # 确保所有的字符串列都是字符串类型
            for col in ['客户简称', '所属区域', '申请人', '产品代码', '产品名称', '订单类型']:
                df[col] = df[col].astype(str)

            # 添加简化产品名称列
            df['简化产品名称'] = df.apply(
                lambda row: get_simplified_product_name(row['产品代码'], row['产品名称']),
                axis=1
            )

            return df
        except Exception as e:
            st.error(f"文件加载失败: {str(e)}。使用示例数据进行演示。")
            return load_sample_data()
    else:
        # 没有文件路径或文件不存在，使用示例数据
        if file_path:
            st.warning(f"文件路径不存在: {file_path}。使用示例数据进行演示。")
        return load_sample_data()


# 创建产品代码到简化产品名称的映射函数 - 修复版本
def get_simplified_product_name(product_code, product_name):
    """
    从产品名称中提取简化产品名称，增强错误处理
    """
    try:
        # 确保输入是字符串类型
        if not isinstance(product_name, str):
            return str(product_code)  # 返回产品代码作为备选

        if '口力' in product_name:
            # 提取"口力"之后的产品类型
            name_parts = product_name.split('口力')
            if len(name_parts) > 1:
                name_part = name_parts[1]
                if '-' in name_part:
                    name_part = name_part.split('-')[0].strip()

                # 进一步简化，只保留主要部分（去掉规格和包装形式）
                for suffix in ['G分享装袋装', 'G盒装', 'G袋装', 'KG迷你包', 'KG随手包']:
                    if suffix in name_part:
                        name_part = name_part.split(suffix)[0]
                        break

                # 去掉可能的数字和单位
                simple_name = re.sub(r'\d+\w*\s*', '', name_part).strip()

                if simple_name:  # 确保简化名称不为空
                    return f"{simple_name} ({product_code})"

        # 如果无法提取或处理中出现错误，则返回产品代码
        return str(product_code)
    except Exception as e:
        # 捕获任何异常，确保函数始终返回一个字符串
        print(f"简化产品名称时出错: {e}，产品代码: {product_code}")
        return str(product_code)


# 创建示例数据（以防用户没有上传文件） - 修复版本
@st.cache_data
def load_sample_data():
    """
    创建示例数据，确保所有列表长度一致
    """
    # 产品代码
    product_codes = [
        'F3415D', 'F3421D', 'F0104J', 'F0104L', 'F3411A', 'F01E4B',
        'F01L4C', 'F01C2P', 'F01E6D', 'F3450B', 'F3415B', 'F0110C',
        'F0183F', 'F01K8A', 'F0183K', 'F0101P'
    ]

    # 产品名称，确保与产品代码数量一致
    product_names = [
        '口力酸小虫250G分享装袋装-中国', '口力可乐瓶250G分享装袋装-中国',
        '口力比萨XXL45G盒装-中国', '口力比萨68G袋装-中国', '口力午餐袋77G袋装-中国',
        '口力汉堡108G袋装-中国', '口力扭扭虫2KG迷你包-中国', '口力字节软糖2KG迷你包-中国',
        '口力西瓜1.5KG随手包-中国', '口力七彩熊1.5KG随手包-中国',
        '口力软糖新品A-中国', '口力软糖新品B-中国', '口力软糖新品C-中国', '口力软糖新品D-中国',
        '口力软糖新品E-中国', '口力软糖新品F-中国'
    ]

    # 客户简称，确保长度一致
    customers = ['广州佳成行', '广州佳成行', '广州佳成行', '广州佳成行', '广州佳成行',
                 '广州佳成行', '河南甜丰號', '河南甜丰號', '河南甜丰號', '河南甜丰號',
                 '河南甜丰號', '广州佳成行', '河南甜丰號', '广州佳成行', '河南甜丰號',
                 '广州佳成行']

    try:
        # 创建简化版示例数据，添加更多变化性
        data = {
            '客户简称': customers,
            '所属区域': ['东', '东', '东', '东', '东', '东', '中', '中', '中', '中', '中',
                         '南', '中', '北', '北', '西'],
            '发运月份': ['2025-03', '2025-03', '2025-03', '2025-03', '2025-03', '2025-03',
                         '2025-03', '2025-03', '2025-03', '2025-03', '2025-03', '2025-03',
                         '2025-03', '2025-03', '2025-03', '2025-03'],
            '申请人': ['梁洪泽', '梁洪泽', '梁洪泽', '梁洪泽', '梁洪泽', '梁洪泽',
                       '胡斌', '胡斌', '胡斌', '胡斌', '胡斌', '梁洪泽', '胡斌', '梁洪泽',
                       '胡斌', '梁洪泽'],
            '产品代码': product_codes,
            '产品名称': product_names,
            '订单类型': ['订单-正常产品'] * 16,
            '单价（箱）': [121.44, 121.44, 216.96, 126.72, 137.04, 137.04, 127.2, 127.2,
                         180, 180, 180, 150, 160, 170, 180, 190],
            '数量（箱）': [10, 10, 20, 50, 252, 204, 7, 2, 6, 6, 6, 30, 20, 15, 10, 5]
        }

        # 创建DataFrame
        df = pd.DataFrame(data)

        # 计算销售额
        df['销售额'] = df['单价（箱）'] * df['数量（箱）']

        # 增加销售额的变化性，避免所有区域都有相同的销售额
        # 通过groupby后乘以不同的随机因子来实现
        region_factors = {'东': 5.2, '南': 3.8, '中': 0.9, '北': 1.6, '西': 1.3}

        # 应用区域因子
        for region, factor in region_factors.items():
            mask = df['所属区域'] == region
            df.loc[mask, '销售额'] = df.loc[mask, '销售额'] * factor

        # 添加简化产品名称
        df['简化产品名称'] = df.apply(
            lambda row: get_simplified_product_name(row['产品代码'], row['产品名称']),
            axis=1
        )

        return df
    except Exception as e:
        # 如果示例数据创建失败，创建一个最小化的DataFrame
        st.error(f"创建示例数据时出错: {str(e)}。使用简化版示例数据。")

        # 创建最简单的数据集
        simple_df = pd.DataFrame({
            '客户简称': ['示例客户A', '示例客户B', '示例客户C'],
            '所属区域': ['东', '南', '中'],
            '发运月份': ['2025-03', '2025-03', '2025-03'],
            '申请人': ['示例申请人A', '示例申请人B', '示例申请人C'],
            '产品代码': ['X001', 'X002', 'X003'],
            '产品名称': ['示例产品A', '示例产品B', '示例产品C'],
            '订单类型': ['订单-正常产品'] * 3,
            '单价（箱）': [100, 150, 200],
            '数量（箱）': [10, 15, 20],
            '销售额': [1000, 2250, 4000],
            '简化产品名称': ['产品A (X001)', '产品B (X002)', '产品C (X003)']
        })

        return simple_df


# 定义默认文件路径
DEFAULT_FILE_PATH = "Q1xlsx.xlsx"

# 侧边栏 - 上传文件区域
st.sidebar.markdown('<div class="sidebar-header">数据导入</div>', unsafe_allow_html=True)
use_default_file = st.sidebar.checkbox("使用默认文件", value=True, help="使用指定的本地文件路径")
uploaded_file = st.sidebar.file_uploader("或上传Excel销售数据文件", type=["xlsx", "xls"], disabled=use_default_file)

# 加载数据
if use_default_file:
    # 使用默认文件路径
    if os.path.exists(DEFAULT_FILE_PATH):
        df = load_data(DEFAULT_FILE_PATH)
        st.sidebar.success(f"已成功加载默认文件: {DEFAULT_FILE_PATH}")
    else:
        st.sidebar.error(f"默认文件路径不存在: {DEFAULT_FILE_PATH}")
        df = load_sample_data()
        st.sidebar.info("正在使用示例数据。请上传您的数据文件获取真实分析。")
elif uploaded_file is not None:
    # 使用上传的文件
    df = load_data(uploaded_file)
else:
    # 没有文件，使用示例数据
    df = load_sample_data()
    st.sidebar.info("正在使用示例数据。请上传您的数据文件获取真实分析。")

# 定义新品产品代码
new_products = ['F0110C', 'F0183F', 'F01K8A', 'F0183K', 'F0101P']
new_products_df = df[df['产品代码'].isin(new_products)]

# 创建产品代码到简化名称的映射字典（用于图表显示）
product_name_mapping = {
    code: df[df['产品代码'] == code]['简化产品名称'].iloc[0] if len(df[df['产品代码'] == code]) > 0 else code
    for code in df['产品代码'].unique()
}

# 侧边栏 - 筛选器
st.sidebar.markdown('<div class="sidebar-header">筛选数据</div>', unsafe_allow_html=True)

# 区域筛选器
all_regions = sorted(df['所属区域'].astype(str).unique())
selected_regions = st.sidebar.multiselect("选择区域", all_regions, default=all_regions)

# 客户筛选器
all_customers = sorted(df['客户简称'].astype(str).unique())
selected_customers = st.sidebar.multiselect("选择客户", all_customers, default=[])

# 产品代码筛选器
all_products = sorted(df['产品代码'].astype(str).unique())
product_options = [(code, product_name_mapping[code]) for code in all_products]
selected_products = st.sidebar.multiselect(
    "选择产品",
    options=all_products,
    format_func=lambda x: f"{x} ({product_name_mapping[x]})",
    default=[]
)

# 申请人筛选器
all_applicants = sorted(df['申请人'].astype(str).unique())
selected_applicants = st.sidebar.multiselect("选择申请人", all_applicants, default=[])

# 应用筛选条件
filtered_df = df.copy()

if selected_regions:
    filtered_df = filtered_df[filtered_df['所属区域'].isin(selected_regions)]

if selected_customers:
    filtered_df = filtered_df[filtered_df['客户简称'].isin(selected_customers)]

if selected_products:
    filtered_df = filtered_df[filtered_df['产品代码'].isin(selected_products)]

if selected_applicants:
    filtered_df = filtered_df[filtered_df['申请人'].isin(selected_applicants)]

# 根据筛选后的数据筛选新品数据
filtered_new_products_df = filtered_df[filtered_df['产品代码'].isin(new_products)]

# 导航栏
st.markdown('<div class="sub-header">导航</div>', unsafe_allow_html=True)
tabs = st.tabs(["销售概览", "新品分析", "客户细分", "产品组合", "市场渗透率"])

with tabs[0]:  # 销售概览
    # KPI指标行
    st.markdown('<div class="sub-header"> 🔑 关键绩效指标</div>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_sales = filtered_df['销售额'].sum()
        st.markdown(f"""
        <div class="card">
            <div class="metric-label">总销售额</div>
            <div class="metric-value">{format_yuan(total_sales)}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        total_customers = filtered_df['客户简称'].nunique()
        st.markdown(f"""
        <div class="card">
            <div class="metric-label">客户数量</div>
            <div class="metric-value">{total_customers}</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        total_products = filtered_df['产品代码'].nunique()
        st.markdown(f"""
        <div class="card">
            <div class="metric-label">产品数量</div>
            <div class="metric-value">{total_products}</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        avg_price = filtered_df['单价（箱）'].mean()
        st.markdown(f"""
        <div class="card">
            <div class="metric-label">平均单价</div>
            <div class="metric-value">{avg_price:.2f}元</div>
        </div>
        """, unsafe_allow_html=True)

    # 区域销售分析
    st.markdown('<div class="sub-header section-gap"> 📊 区域销售分析</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        # 区域销售额柱状图 - 使用go.Figure和go.Bar代替px.bar以修复标签问题
        region_sales = filtered_df.groupby('所属区域')['销售额'].sum().reset_index()

        # 创建空figure
        fig_region = go.Figure()

        # 为每个区域添加单独的柱状图
        colors = px.colors.qualitative.Bold
        for i, row in region_sales.iterrows():
            region = row['所属区域']
            sales = row['销售额']
            color_idx = i % len(colors)

            fig_region.add_trace(go.Bar(
                x=[region],
                y=[sales],
                name=region,
                marker_color=colors[color_idx],
                text=[f"{format_yuan(sales)}"],
                textposition='outside',
                textfont=dict(size=14)
            ))

        # 更新布局
        fig_region.update_layout(
            title='各区域销售额',
            xaxis_title=dict(text="区域", font=dict(size=16)),
            yaxis_title=dict(text="销售额 (元)", font=dict(size=16)),
            xaxis_tickfont=dict(size=14),
            yaxis_tickfont=dict(size=14),
            margin=dict(t=60, b=100, l=100, r=80),
            plot_bgcolor='rgba(0,0,0,0)',
            barmode='group',
            showlegend=False
        )

        # 确保Y轴有足够空间显示数据标签
        fig_region.update_yaxes(
            range=[0, region_sales['销售额'].max() * 1.3],
            tickformat=',',
            type='linear'
        )

        st.plotly_chart(fig_region, use_container_width=True)

    with col2:
        # 修改区域销售占比饼图代码
        if not filtered_df.empty and not region_sales.empty:
            fig_region_pie = px.pie(
                region_sales,
                values='销售额',
                names='所属区域',
                title='各区域销售占比',
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            fig_region_pie.update_traces(
                textposition='inside',
                textinfo='percent+label',
                texttemplate='%{label}<br>%{percent:.2f}%',  # 修改：强制保留2位小数
                textfont=dict(size=14)
            )
            fig_region_pie.update_layout(
                margin=dict(t=60, b=60, l=60, r=60),
                font=dict(size=14)
            )
            st.plotly_chart(fig_region_pie, use_container_width=True)
        else:
            st.warning("当前筛选条件下没有数据可显示。")

    # 产品销售分析
    st.markdown('<div class="sub-header section-gap"> 📦 产品销售分析</div>', unsafe_allow_html=True)

    # 为所有图表添加此配置，只保留下载图片功能
    config = {
        'displayModeBar': True,
        'modeBarButtonsToRemove': [
            'zoom2d', 'pan2d', 'select2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d',
            'autoScale2d', 'resetScale2d', 'toggleSpikelines', 'hoverClosestCartesian',
            'hoverCompareCartesian', 'toImage', 'sendDataToCloud', 'toggleHover',
            'resetViews', 'toggleOrientationY', 'toggleOrientationX'
        ],
        'modeBarButtonsToAdd': []
    }


    # 修复提取包装类型的函数
    def extract_packaging(product_name):
        """
        提取产品名称中的包装类型，增强错误处理
        """
        try:
            # 确保产品名称是字符串
            if not isinstance(product_name, str):
                return "其他"

            # 检查组合类型
            if '分享装袋装' in product_name:
                return '分享装袋装'
            elif '分享装盒装' in product_name:
                return '分享装盒装'

            # 按包装大小分类（从大到小）
            elif '随手包' in product_name:
                return '随手包'
            elif '迷你包' in product_name:
                return '迷你包'
            elif '分享装' in product_name:
                return '分享装'

            # 按包装形式分类
            elif '袋装' in product_name:
                return '袋装'
            elif '盒装' in product_name:
                return '盒装'

            # 处理特殊规格
            elif 'KG' in product_name or 'kg' in product_name:
                if '1.5KG' in product_name or '1.5kg' in product_name:
                    return '大包装'
                elif '2KG' in product_name or '2kg' in product_name:
                    return '大包装'
                else:
                    return '散装'
            elif 'G' in product_name:
                match = re.search(r'(\d+)G', product_name)
                if match:
                    weight = int(match.group(1))
                    if weight <= 50:
                        return '小包装'
                    elif weight <= 100:
                        return '中包装'
                    else:
                        return '大包装'

            # 默认分类
            return '其他'
        except:
            return '其他'  # 捕获任何异常并返回默认值


    filtered_df['包装类型'] = filtered_df['产品名称'].apply(extract_packaging)
    packaging_sales = filtered_df.groupby('包装类型')['销售额'].sum().reset_index()

    col1, col2 = st.columns(2)

    with col1:
        # 包装类型销售额柱状图 - 使用go.Figure修复标签问题
        packaging_sales = packaging_sales.sort_values(by='销售额', ascending=False)

        fig_packaging = go.Figure()

        # 为每个包装类型添加单独的柱状图
        colors = px.colors.qualitative.Plotly
        for i, row in packaging_sales.iterrows():
            package_type = row['包装类型']
            sales = row['销售额']
            color_idx = i % len(colors)

            fig_packaging.add_trace(go.Bar(
                x=[package_type],
                y=[sales],
                name=package_type,
                marker_color=colors[color_idx],
                text=[f"{format_yuan(sales)}"],
                textposition='outside',
                textfont=dict(size=14)
            ))

        # 更新布局
        fig_packaging.update_layout(
            title='不同包装类型销售额',
            xaxis_title=dict(text="包装类型", font=dict(size=16)),
            yaxis_title=dict(text="销售额 (人民币)", font=dict(size=16)),
            xaxis_tickfont=dict(size=14),
            yaxis_tickfont=dict(size=14),
            margin=dict(t=60, b=80, l=80, r=60),
            plot_bgcolor='rgba(0,0,0,0)',
            barmode='group',
            showlegend=False
        )

        # 确保Y轴有足够空间显示数据标签
        fig_packaging.update_yaxes(
            range=[0, packaging_sales['销售额'].max() * 1.2],
            tickformat=',',
            type='linear'
        )

        st.plotly_chart(fig_packaging, use_container_width=True)

    with col2:
        # 价格-销量散点图
        fig_price_qty = px.scatter(
            filtered_df,
            x='单价（箱）',
            y='数量（箱）',
            size='销售额',
            color='所属区域',
            hover_name='简化产品名称',  # 使用简化产品名称
            title='价格与销售数量关系',
            labels={'单价（箱）': '单价 (元/箱)', '数量（箱）': '销售数量 (箱)'},
            height=500
        )

        # 修复x轴单位显示
        fig_price_qty.update_xaxes(
            tickprefix='¥',  # 添加货币前缀
            tickformat=',',  # 使用千位分隔符
            ticksuffix='元',  # 添加货币后缀
            type='linear',  # 强制使用线性刻度
            separatethousands=True  # 强制使用千位分隔符
        )

        # 添加趋势线
        fig_price_qty.update_layout(
            xaxis_title=dict(text="单价 (元/箱)", font=dict(size=16)),
            yaxis_title=dict(text="销售数量 (箱)", font=dict(size=16)),
            xaxis_tickfont=dict(size=14),
            yaxis_tickfont=dict(size=14),
            margin=dict(t=60, b=80, l=80, r=60),
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_price_qty, use_container_width=True)

    # 申请人销售业绩
    st.markdown('<div class="sub-header section-gap"> 👨‍💼 申请人销售业绩</div>', unsafe_allow_html=True)
    applicant_performance = filtered_df.groupby('申请人')['销售额'].sum().sort_values(ascending=False).reset_index()

    # 申请人销售业绩 - 使用go.Figure修复标签问题
    fig_applicant = go.Figure()

    # 为每个申请人添加单独的柱状图
    colors = px.colors.qualitative.Safe
    for i, row in applicant_performance.iterrows():
        applicant = row['申请人']
        sales = row['销售额']
        color_idx = i % len(colors)

        fig_applicant.add_trace(go.Bar(
            x=[applicant],
            y=[sales],
            name=applicant,
            marker_color=colors[color_idx],
            text=[f"{format_yuan(sales)}"],
            textposition='outside',
            textfont=dict(size=14)
        ))

    # 更新布局
    fig_applicant.update_layout(
        title='申请人销售业绩排名',
        xaxis_title=dict(text="申请人", font=dict(size=16)),
        yaxis_title=dict(text="销售额 (人民币)", font=dict(size=16)),
        xaxis_tickfont=dict(size=14),
        yaxis_tickfont=dict(size=14),
        margin=dict(t=60, b=80, l=80, r=60),
        plot_bgcolor='rgba(0,0,0,0)',
        barmode='group',
        showlegend=False
    )

    # 确保Y轴有足够空间显示数据标签
    fig_applicant.update_yaxes(
        range=[0, applicant_performance['销售额'].max() * 1.2],
        tickformat=',',
        type='linear'
    )

    st.plotly_chart(fig_applicant, use_container_width=True)

    # 原始数据表
    with st.expander("查看筛选后的原始数据"):
        st.dataframe(filtered_df)

with tabs[1]:  # 新品分析
    st.markdown('<div class="sub-header"> 🆕 新品销售分析</div>', unsafe_allow_html=True)

    # 新品KPI指标
    col1, col2, col3 = st.columns(3)

    with col1:
        new_products_sales = filtered_new_products_df['销售额'].sum()
        st.markdown(f"""
        <div class="card">
            <div class="metric-label">新品销售额</div>
            <div class="metric-value">{format_yuan(new_products_sales)}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        new_products_percentage = (new_products_sales / total_sales * 100) if total_sales > 0 else 0
        st.markdown(f"""
        <div class="card">
            <div class="metric-label">新品销售占比</div>
            <div class="metric-value">{new_products_percentage:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        new_products_customers = filtered_new_products_df['客户简称'].nunique()
        st.markdown(f"""
        <div class="card">
            <div class="metric-label">购买新品的客户数</div>
            <div class="metric-value">{new_products_customers}</div>
        </div>
        """, unsafe_allow_html=True)

    # 新品销售详情
    st.markdown('<div class="sub-header section-gap">各新品销售额对比</div>', unsafe_allow_html=True)

    if not filtered_new_products_df.empty:
        # 使用简化产品名称
        product_sales = filtered_new_products_df.groupby(['产品代码', '简化产品名称'])['销售额'].sum().reset_index()
        product_sales = product_sales.sort_values('销售额', ascending=False)

        # 使用go.Figure修复标签问题
        fig_product_sales = go.Figure()

        # 为每个产品添加单独的柱状图
        colors = px.colors.qualitative.Pastel
        for i, row in product_sales.iterrows():
            product = row['简化产品名称']
            sales = row['销售额']
            color_idx = i % len(colors)

            fig_product_sales.add_trace(go.Bar(
                x=[product],
                y=[sales],
                name=product,
                marker_color=colors[color_idx],
                text=[f"{format_yuan(sales)}"],
                textposition='outside',
                textfont=dict(size=14)
            ))

        # 更新布局
        fig_product_sales.update_layout(
            title='新品产品销售额对比',
            xaxis_title=dict(text="产品名称", font=dict(size=16)),
            yaxis_title=dict(text="销售额 (人民币)", font=dict(size=16)),
            xaxis_tickfont=dict(size=14),
            yaxis_tickfont=dict(size=14),
            margin=dict(t=60, b=80, l=80, r=60),
            plot_bgcolor='rgba(0,0,0,0)',
            barmode='group',
            showlegend=False
        )

        # 确保Y轴有足够空间显示数据标签
        fig_product_sales.update_yaxes(
            range=[0, product_sales['销售额'].max() * 1.2],
            tickformat=',',
            type='linear'
        )

        st.plotly_chart(fig_product_sales, use_container_width=True)

        # 区域新品销售分析
        st.markdown('<div class="sub-header section-gap">区域新品销售分析</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)

        with col1:
            # 区域新品销售额堆叠柱状图
            region_product_sales = filtered_new_products_df.groupby(['所属区域', '简化产品名称'])[
                '销售额'].sum().reset_index()
            fig_region_product = px.bar(
                region_product_sales,
                x='所属区域',
                y='销售额',
                color='简化产品名称',
                title='各区域新品销售额分布',
                labels={'销售额': '销售额 (元)', '所属区域': '区域', '简化产品名称': '产品名称'},
                height=500
            )
            # 不要直接设置固定文本标签
            fig_region_product.update_layout(
                xaxis_title=dict(text="区域", font=dict(size=16)),
                yaxis_title=dict(text="销售额 (元)", font=dict(size=16)),
                xaxis_tickfont=dict(size=14),
                yaxis_tickfont=dict(size=14),
                margin=dict(t=60, b=80, l=80, r=60),
                plot_bgcolor='rgba(0,0,0,0)',
                legend_title="产品名称",
                legend_font=dict(size=12)
            )
            # 添加以下代码修复y轴
            fig_region_product.update_yaxes(
                tickformat=',',
                type='linear'
            )
            st.plotly_chart(fig_region_product, use_container_width=True)

        with col2:
            # 新品占比饼图
            fig_new_vs_old = px.pie(
                values=[new_products_sales, total_sales - new_products_sales],
                names=['新品', '非新品'],
                title='新品销售额占总销售额比例',
                hole=0.4,
                color_discrete_sequence=['#ff9999', '#66b3ff']
            )
            fig_new_vs_old.update_traces(
                textposition='inside',
                textinfo='percent+label',
                textfont=dict(size=14)
            )
            fig_new_vs_old.update_layout(
                margin=dict(t=60, b=60, l=60, r=60),
                font=dict(size=14)
            )
            st.plotly_chart(fig_new_vs_old, use_container_width=True)

        # 区域内新品销售占比热力图
        st.markdown('<div class="sub-header section-gap">各区域内新品销售占比</div>', unsafe_allow_html=True)

        # 计算各区域的新品总销售额
        region_total_sales = filtered_new_products_df.groupby('所属区域')['销售额'].sum().reset_index()

        # 计算各区域各新品的销售占比
        region_product_sales = filtered_new_products_df.groupby(['所属区域', '产品代码', '简化产品名称'])[
            '销售额'].sum().reset_index()
        region_product_sales = region_product_sales.merge(region_total_sales, on='所属区域', suffixes=('', '_区域总计'))
        region_product_sales['销售占比'] = region_product_sales['销售额'] / region_product_sales[
            '销售额_区域总计'] * 100

        # 创建显示名称列（简化产品名称）
        region_product_sales['显示名称'] = region_product_sales['简化产品名称']

        # 透视表
        pivot_percentage = pd.pivot_table(
            region_product_sales,
            values='销售占比',
            index='所属区域',
            columns='显示名称',  # 使用简化名称作为列名
            fill_value=0
        )

        # 使用Plotly创建热力图
        fig_heatmap = px.imshow(
            pivot_percentage,
            labels=dict(x="产品名称", y="区域", color="销售占比 (%)"),
            x=pivot_percentage.columns,
            y=pivot_percentage.index,
            color_continuous_scale="YlGnBu",
            title="各区域内新品销售占比 (%)",
            height=500
        )

        fig_heatmap.update_layout(
            xaxis_title=dict(text="产品名称", font=dict(size=16)),
            yaxis_title=dict(text="区域", font=dict(size=16)),
            margin=dict(t=80, b=80, l=100, r=100),
            font=dict(size=14)
        )

        # 修改热力图注释代码
        for i in range(len(pivot_percentage.index)):
            for j in range(len(pivot_percentage.columns)):
                fig_heatmap.add_annotation(
                    x=j,
                    y=i,
                    text=f"{pivot_percentage.iloc[i, j]:.2f}%",  # 修改：强制保留2位小数
                    showarrow=False,
                    font=dict(color="black" if pivot_percentage.iloc[i, j] < 50 else "white", size=14)
                )

        st.plotly_chart(fig_heatmap, use_container_width=True)
    else:
        st.warning("当前筛选条件下没有新品数据。请调整筛选条件或确认数据中包含新品。")

    # 新品数据表
    with st.expander("查看新品销售数据"):
        if not filtered_new_products_df.empty:
            display_columns = [col for col in filtered_new_products_df.columns if
                               col != '产品代码' or col != '产品名称']
            st.dataframe(filtered_new_products_df[display_columns])
        else:
            st.info("当前筛选条件下没有新品数据。")

with tabs[2]:  # 客户细分
    st.markdown('<div class="sub-header"> 👥 客户细分分析</div>', unsafe_allow_html=True)

    if not filtered_df.empty:
        # 计算客户特征
        customer_features = filtered_df.groupby('客户简称').agg({
            '销售额': 'sum',  # 总销售额
            '产品代码': lambda x: len(set(x)),  # 购买的不同产品数量
            '数量（箱）': 'sum',  # 总购买数量
            '单价（箱）': 'mean'  # 平均单价
        }).reset_index()

        # 添加新品购买指标
        new_products_by_customer = filtered_new_products_df.groupby('客户简称')['销售额'].sum().reset_index()
        customer_features = customer_features.merge(new_products_by_customer, on='客户简称', how='left',
                                                    suffixes=('', '_新品'))
        customer_features['销售额_新品'] = customer_features['销售额_新品'].fillna(0)
        customer_features['新品占比'] = customer_features['销售额_新品'] / customer_features['销售额'] * 100

        # 简单客户分类
        customer_features['客户类型'] = pd.cut(
            customer_features['新品占比'],
            bins=[0, 10, 30, 100],
            labels=['保守型客户', '平衡型客户', '创新型客户']
        )

        # 添加客户类型解释
        st.markdown('<div class="highlight" style="margin-bottom: 20px;">', unsafe_allow_html=True)
        st.markdown("""
        <h3 style="font-size: 1.3rem; color: #1E88E5; margin-bottom: 10px;">客户类型解释说明</h3>
        <p><strong>保守型客户</strong>：新品销售占比在0-10%之间，对新品接受度较低，倾向于购买成熟稳定的产品。</p>
        <p><strong>平衡型客户</strong>：新品销售占比在10-30%之间，对新品有一定接受度，同时保持对现有产品的购买。</p>
        <p><strong>创新型客户</strong>：新品销售占比在30-100%之间，积极尝试新品，是推广新产品的重要客户群体。</p>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # 客户分类展示
        st.markdown('<div class="sub-header section-gap">客户类型分布</div>', unsafe_allow_html=True)

        simple_segments = customer_features.groupby('客户类型').agg({
            '客户简称': 'count',
            '销售额': 'mean',
            '新品占比': 'mean'
        }).reset_index()

        simple_segments.columns = ['客户类型', '客户数量', '平均销售额', '平均新品占比']

        # 使用go.Figure修复标签问题 - 客户类型分布图
        fig_customer_types = go.Figure()

        # 为每个客户类型添加单独的柱状图
        colors = px.colors.qualitative.Bold
        for i, row in simple_segments.iterrows():
            customer_type = row['客户类型']
            count = row['客户数量']
            color_idx = i % len(colors)

            fig_customer_types.add_trace(go.Bar(
                x=[customer_type],
                y=[count],
                name=customer_type,
                marker_color=colors[color_idx],
                text=[count],
                textposition='outside',
                textfont=dict(size=14)
            ))

        # 更新布局
        fig_customer_types.update_layout(
            title='客户类型分布',
            xaxis_title=dict(text="客户类型", font=dict(size=16)),
            yaxis_title=dict(text="客户数量", font=dict(size=16)),
            xaxis_tickfont=dict(size=14),
            yaxis_tickfont=dict(size=14),
            margin=dict(t=60, b=80, l=80, r=60),
            plot_bgcolor='rgba(0,0,0,0)',
            barmode='group',
            showlegend=False
        )

        # 确保Y轴有足够空间显示数据标签
        fig_customer_types.update_yaxes(
            range=[0, simple_segments['客户数量'].max() * 1.2]
        )

        st.plotly_chart(fig_customer_types, use_container_width=True)

        # 客户类型特征对比
        st.markdown('<div class="sub-header section-gap">不同客户类型的特征对比</div>', unsafe_allow_html=True)

        # 创建子图 - 优化版
        fig = make_subplots(rows=1, cols=2,
                            subplot_titles=("客户类型平均销售额", "客户类型平均新品占比"),
                            specs=[[{"type": "bar"}, {"type": "bar"}]])

        # 添加平均销售额柱状图
        for i, row in simple_segments.iterrows():
            customer_type = row['客户类型']
            avg_sales = row['平均销售额']

            fig.add_trace(
                go.Bar(
                    x=[customer_type],
                    y=[avg_sales],
                    name=f"{customer_type} - 销售额",
                    marker_color='rgb(55, 83, 109)',
                    text=[f"{format_yuan(avg_sales)}"],
                    textposition='outside',
                    textfont=dict(size=14)
                ),
                row=1, col=1
            )

        # 添加平均新品占比柱状图
        for i, row in simple_segments.iterrows():
            customer_type = row['客户类型']
            avg_new_ratio = row['平均新品占比']

            fig.add_trace(
                go.Bar(
                    x=[customer_type],
                    y=[avg_new_ratio],
                    name=f"{customer_type} - 新品占比",
                    marker_color='rgb(26, 118, 255)',
                    text=[f"{avg_new_ratio:.2f}%"],  # 修改为2位小数
                    textposition='outside',
                    textfont=dict(size=14)
                ),
                row=1, col=2
            )

        # 优化图表布局
        fig.update_layout(
            height=500,  # 增加高度
            showlegend=False,
            margin=dict(t=80, b=80, l=80, r=80),  # 增加边距
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(
                family="Arial, sans-serif",
                size=14,  # 增加字体大小
                color="rgb(50, 50, 50)"
            ),
            title_font=dict(size=18)  # 标题字体大小
        )

        # 优化X轴和Y轴
        fig.update_xaxes(
            title_text="客户类型",
            title_font=dict(size=16),
            tickfont=dict(size=14),
            row=1, col=1
        )

        fig.update_yaxes(
            title_text="平均销售额 (元)",
            title_font=dict(size=16),
            tickfont=dict(size=14),
            tickformat=",",  # 添加千位分隔符
            row=1, col=1
        )

        fig.update_xaxes(
            title_text="客户类型",
            title_font=dict(size=16),
            tickfont=dict(size=14),
            row=1, col=2
        )

        fig.update_yaxes(
            title_text="平均新品占比 (%)",
            title_font=dict(size=16),
            tickfont=dict(size=14),
            row=1, col=2
        )

        # 确保Y轴有足够空间显示数据标签
        fig.update_yaxes(range=[0, simple_segments['平均销售额'].max() * 1.3], row=1, col=1)
        fig.update_yaxes(range=[0, simple_segments['平均新品占比'].max() * 1.3], row=1, col=2)

        st.plotly_chart(fig, use_container_width=True)

        # 客户销售额和新品占比散点图
        st.markdown('<div class="sub-header section-gap">客户销售额与新品占比关系</div>', unsafe_allow_html=True)

        fig_scatter = px.scatter(
            customer_features,
            x='销售额',
            y='新品占比',
            color='客户类型',
            size='产品代码',  # 购买的产品种类数量
            hover_name='客户简称',
            title='客户销售额与新品占比关系',
            labels={
                '销售额': '销售额 (元)',
                '新品占比': '新品销售占比 (%)',
                '产品代码': '购买产品种类数'
            },
            height=500
        )

        # 修复销售额单位显示
        fig_scatter.update_xaxes(
            tickprefix='¥',  # 添加货币前缀
            tickformat=',',  # 使用千位分隔符
            ticksuffix='元',  # 添加货币后缀
            type='linear',  # 强制使用线性刻度
            separatethousands=True  # 强制使用千位分隔符
        )

        fig_scatter.update_layout(
            xaxis_title=dict(text="销售额 (元)", font=dict(size=16)),
            yaxis_title=dict(text="新品销售占比 (%)", font=dict(size=16)),
            xaxis_tickfont=dict(size=14),
            yaxis_tickfont=dict(size=14),
            margin=dict(t=60, b=80, l=80, r=60),
            plot_bgcolor='rgba(0,0,0,0)',
            legend_font=dict(size=14)
        )

        st.plotly_chart(fig_scatter, use_container_width=True)

        # 新品接受度最高的客户
        st.markdown('<div class="sub-header section-gap">新品接受度最高的客户</div>', unsafe_allow_html=True)

        top_acceptance = customer_features.sort_values('新品占比', ascending=False).head(10)

        # 使用go.Figure修复标签问题 - 新品接受度最高的客户
        fig_top_acceptance = go.Figure()

        # 为每个客户添加单独的柱状图
        colors = px.colors.sequential.Viridis
        color_scale = px.colors.sequential.Viridis

        # 计算颜色比例
        max_val = top_acceptance['新品占比'].max()
        min_val = top_acceptance['新品占比'].min()
        color_range = max_val - min_val

        # 为每个柱子添加颜色
        for i, row in top_acceptance.iterrows():
            customer = row['客户简称']
            ratio = row['新品占比']

            # 计算颜色索引
            if color_range > 0:
                color_idx = int(((ratio - min_val) / color_range) * (len(color_scale) - 1))
            else:
                color_idx = 0

            fig_top_acceptance.add_trace(go.Bar(
                x=[customer],
                y=[ratio],
                name=customer,
                marker_color=color_scale[color_idx],
                text=[f"{ratio:.2f}%"],  # 修改为2位小数
                textposition='outside',
                textfont=dict(size=14)
            ))

        # 更新布局
        fig_top_acceptance.update_layout(
            title='新品接受度最高的前10名客户',
            xaxis_title=dict(text="客户", font=dict(size=16)),
            yaxis_title=dict(text="新品销售占比 (%)", font=dict(size=16)),
            xaxis_tickfont=dict(size=14),
            yaxis_tickfont=dict(size=14),
            margin=dict(t=60, b=80, l=80, r=60),
            plot_bgcolor='rgba(0,0,0,0)',
            barmode='group',
            showlegend=False
        )

        # 确保Y轴有足够空间显示数据标签
        fig_top_acceptance.update_yaxes(
            range=[0, top_acceptance['新品占比'].max() * 1.2]
        )

        st.plotly_chart(fig_top_acceptance, use_container_width=True)

        # 客户表格
        with st.expander("查看客户细分数据"):
            st.dataframe(customer_features)
    else:
        st.warning("当前筛选条件下没有客户数据。请调整筛选条件。")

with tabs[3]:  # 产品组合
    st.markdown('<div class="sub-header"> 🔄 产品组合分析</div>', unsafe_allow_html=True)

    if not filtered_df.empty and len(filtered_df['客户简称'].unique()) > 1 and len(
            filtered_df['产品代码'].unique()) > 1:
        # 共现矩阵分析
        st.markdown('<div class="sub-header section-gap">产品共现矩阵分析</div>', unsafe_allow_html=True)
        st.info("共现矩阵显示不同产品一起被同一客户购买的频率，有助于发现产品间的关联。")

        # 准备数据 - 创建交易矩阵
        transaction_data = filtered_df.groupby(['客户简称', '产品代码'])['销售额'].sum().unstack().fillna(0)
        # 转换为二进制格式（是否购买）
        transaction_binary = transaction_data.applymap(lambda x: 1 if x > 0 else 0)

        # 创建产品共现矩阵
        co_occurrence = pd.DataFrame(0, index=transaction_binary.columns, columns=transaction_binary.columns)

        # 创建产品代码到简化名称的映射
        name_mapping = {code: df[df['产品代码'] == code]['简化产品名称'].iloc[0]
        if len(df[df['产品代码'] == code]) > 0 else code
                        for code in transaction_binary.columns}

        # 计算共现次数
        for _, row in transaction_binary.iterrows():
            bought_products = row.index[row == 1].tolist()
            for p1 in bought_products:
                for p2 in bought_products:
                    if p1 != p2:
                        co_occurrence.loc[p1, p2] += 1

        # 筛选新品的共现情况
        new_product_co_occurrence = pd.DataFrame()
        valid_new_products = [p for p in new_products if p in co_occurrence.index]

        if valid_new_products:
            for np_code in valid_new_products:
                top_co = co_occurrence.loc[np_code].sort_values(ascending=False).head(5)
                new_product_co_occurrence[np_code] = top_co

            # 可视化每个新品的前5个共现产品
            for np_code in valid_new_products:
                np_name = name_mapping.get(np_code, np_code)  # 获取新品的简化名称
                st.markdown(f'<div class="sub-header">与"{np_name}"共同购买最多的产品</div>', unsafe_allow_html=True)

                co_data = co_occurrence.loc[np_code].sort_values(ascending=False).head(5).reset_index()
                co_data.columns = ['产品代码', '共现次数']

                # 添加简化产品名称
                co_data['简化产品名称'] = co_data['产品代码'].map(name_mapping)

                # 使用go.Figure修复标签问题 - 共现产品图
                fig_co = go.Figure()

                # 为每个产品添加单独的柱状图
                colors = px.colors.qualitative.G10
                for i, row in co_data.iterrows():
                    product = row['简化产品名称']
                    count = row['共现次数']
                    color_idx = i % len(colors)

                    fig_co.add_trace(go.Bar(
                        x=[product],
                        y=[count],
                        name=product,
                        marker_color=colors[color_idx],
                        text=[count],
                        textposition='outside',
                        textfont=dict(size=14)
                    ))

                # 更新布局
                fig_co.update_layout(
                    title=f'与{np_name}共同购买最多的产品',
                    xaxis_title=dict(text="产品名称", font=dict(size=16)),
                    yaxis_title=dict(text="共同购买次数", font=dict(size=16)),
                    xaxis_tickfont=dict(size=14),
                    yaxis_tickfont=dict(size=14),
                    margin=dict(t=60, b=80, l=80, r=60),
                    plot_bgcolor='rgba(0,0,0,0)',
                    barmode='group',
                    showlegend=False
                )

                # 确保Y轴有足够空间显示数据标签
                fig_co.update_yaxes(
                    range=[0, co_data['共现次数'].max() * 1.2]
                )

                st.plotly_chart(fig_co, use_container_width=True)

            # 热力图展示所有产品的共现关系
            st.markdown('<div class="sub-header section-gap">产品共现热力图</div>', unsafe_allow_html=True)
            st.info("热力图显示产品之间的共现关系，颜色越深表示两个产品一起购买的频率越高。")

            # 筛选主要产品以避免图表过于复杂
            top_products = filtered_df.groupby('产品代码')['销售额'].sum().sort_values(ascending=False).head(
                10).index.tolist()
            # 确保所有新品都包含在内
            for np in valid_new_products:
                if np not in top_products:
                    top_products.append(np)

            # 创建简化名称映射的列表
            top_product_names = [name_mapping.get(code, code) for code in top_products]

            # 创建热力图数据
            heatmap_data = co_occurrence.loc[top_products, top_products].copy()

            # 修改共现热力图创建代码
            fig_co_heatmap = px.imshow(
                heatmap_data,
                labels=dict(x="产品名称", y="产品名称", color="共现次数"),
                x=top_product_names,
                y=top_product_names,
                color_continuous_scale="Viridis",
                title="产品共现热力图",
                height=650  # 增加高度
            )

            fig_co_heatmap.update_layout(
                margin=dict(t=80, b=80, l=100, r=100),
                font=dict(size=14),
                xaxis_tickangle=-45  # 倾斜x轴标签以防重叠
            )

            # 更新热力图布局 - 增加边距并调整标签角度
            fig_co_heatmap.update_layout(
                margin=dict(t=80, b=120, l=150, r=100),  # 增加底部和左侧边距
                font=dict(size=14),
                xaxis=dict(
                    tickangle=-45,  # 倾斜x轴标签
                    tickfont=dict(size=12),  # 减小字体
                    automargin=True  # 自动调整边距
                ),
                yaxis=dict(
                    tickfont=dict(size=12),  # 减小字体
                    automargin=True  # 自动调整边距
                )
            )

            # 修改热力图标注字体大小
            for i in range(len(top_products)):
                for j in range(len(top_products)):
                    if heatmap_data.iloc[i, j] > 0:  # 只显示非零值
                        fig_co_heatmap.add_annotation(
                            x=j,
                            y=i,
                            text=f"{int(heatmap_data.iloc[i, j])}",
                            showarrow=False,
                            font=dict(
                                color="white" if heatmap_data.iloc[i, j] > heatmap_data.max().max() / 2 else "black",
                                size=11  # 减小标注字体大小
                            )
                        )

            # 添加数值注释 - 修复显示准确性
            for i in range(len(top_products)):
                for j in range(len(top_products)):
                    if heatmap_data.iloc[i, j] > 0:  # 只显示非零值
                        fig_co_heatmap.add_annotation(
                            x=j,
                            y=i,
                            text=f"{int(heatmap_data.iloc[i, j])}",  # 使用整数显示
                            showarrow=False,
                            font=dict(
                                color="white" if heatmap_data.iloc[i, j] > heatmap_data.max().max() / 2 else "black",
                                size=12)
                        )

            st.plotly_chart(fig_co_heatmap, use_container_width=True)
        else:
            st.warning("在当前筛选条件下，未找到新品数据或共现关系。")

        # 产品购买模式
        st.markdown('<div class="sub-header section-gap">产品购买模式分析</div>', unsafe_allow_html=True)

        # 计算平均每单购买的产品种类数
        avg_products_per_order = transaction_binary.sum(axis=1).mean()

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"""
            <div class="card">
                <div class="metric-label">平均每客户购买产品种类</div>
                <div class="metric-value">{avg_products_per_order:.2f}</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            # 计算含有新品的订单比例
            orders_with_new_products = transaction_binary[valid_new_products].any(
                axis=1).sum() if valid_new_products else 0
            total_orders = len(transaction_binary)
            percentage_orders_with_new = (orders_with_new_products / total_orders * 100) if total_orders > 0 else 0

            st.markdown(f"""
            <div class="card">
                <div class="metric-label">含新品的客户比例</div>
                <div class="metric-value">{percentage_orders_with_new:.2f}%</div>
            </div>
            """, unsafe_allow_html=True)

        # 购买产品种类数分布
        products_per_order = transaction_binary.sum(axis=1).value_counts().sort_index().reset_index()
        products_per_order.columns = ['产品种类数', '客户数']

        # 使用go.Figure修复标签问题 - 购买产品种类数分布
        fig_products_dist = go.Figure()

        # 为每个产品种类数添加单独的柱状图
        for i, row in products_per_order.iterrows():
            category_count = row['产品种类数']
            customer_count = row['客户数']

            fig_products_dist.add_trace(go.Bar(
                x=[category_count],
                y=[customer_count],
                name=str(category_count),
                text=[customer_count],
                textposition='outside',
                textfont=dict(size=14)
            ))

        # 更新布局
        fig_products_dist.update_layout(
            title='客户购买产品种类数分布',
            xaxis_title=dict(text="购买产品种类数", font=dict(size=16)),
            yaxis_title=dict(text="客户数量", font=dict(size=16)),
            xaxis_tickfont=dict(size=14),
            yaxis_tickfont=dict(size=14),
            margin=dict(t=60, b=80, l=80, r=60),
            plot_bgcolor='rgba(0,0,0,0)',
            barmode='group',
            showlegend=False
        )

        # 确保Y轴有足够空间显示数据标签
        fig_products_dist.update_yaxes(
            range=[0, products_per_order['客户数'].max() * 1.2]
        )

        st.plotly_chart(fig_products_dist, use_container_width=True)

        # 产品组合表格
        with st.expander("查看产品共现矩阵"):
            # 转换产品代码为简化名称
            display_co_occurrence = co_occurrence.copy()
            display_co_occurrence.index = [name_mapping.get(code, code) for code in display_co_occurrence.index]
            display_co_occurrence.columns = [name_mapping.get(code, code) for code in display_co_occurrence.columns]
            st.dataframe(display_co_occurrence)
    else:
        st.warning("当前筛选条件下的数据不足以进行产品组合分析。请确保有多个客户和产品。")

with tabs[4]:  # 市场渗透率
    st.markdown('<div class="sub-header"> 🌐 新品市场渗透率分析</div>', unsafe_allow_html=True)

    if not filtered_df.empty:
        # 计算总体渗透率
        total_customers = filtered_df['客户简称'].nunique()
        new_product_customers = filtered_new_products_df['客户简称'].nunique()
        penetration_rate = (new_product_customers / total_customers * 100) if total_customers > 0 else 0

        # KPI指标
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(f"""
            <div class="card">
                <div class="metric-label">总客户数</div>
                <div class="metric-value">{total_customers}</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="card">
                <div class="metric-label">购买新品的客户数</div>
                <div class="metric-value">{new_product_customers}</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="card">
                <div class="metric-label">新品市场渗透率</div>
                <div class="metric-value">{penetration_rate:.2f}%</div>
            </div>
            """, unsafe_allow_html=True)

        # 区域渗透率分析
        st.markdown('<div class="sub-header section-gap">各区域新品渗透率</div>', unsafe_allow_html=True)

        if 'selected_regions' in locals() and selected_regions:
            # 按区域计算渗透率
            region_customers = filtered_df.groupby('所属区域')['客户简称'].nunique().reset_index()
            region_customers.columns = ['所属区域', '客户总数']

            new_region_customers = filtered_new_products_df.groupby('所属区域')['客户简称'].nunique().reset_index()
            new_region_customers.columns = ['所属区域', '购买新品客户数']

            region_penetration = region_customers.merge(new_region_customers, on='所属区域', how='left')
            region_penetration['购买新品客户数'] = region_penetration['购买新品客户数'].fillna(0)
            region_penetration['渗透率'] = (
                    region_penetration['购买新品客户数'] / region_penetration['客户总数'] * 100).round(2)

            # 使用go.Figure修复标签问题 - 区域渗透率
            fig_region_penetration = go.Figure()

            # 为每个区域添加单独的柱状图
            colors = px.colors.qualitative.Bold
            for i, row in region_penetration.iterrows():
                region = row['所属区域']
                penetration = row['渗透率']
                color_idx = i % len(colors)

                fig_region_penetration.add_trace(go.Bar(
                    x=[region],
                    y=[penetration],
                    name=region,
                    marker_color=colors[color_idx],
                    text=[f"{penetration:.2f}%"],
                    textposition='outside',
                    textfont=dict(size=14)
                ))

            # 更新布局
            fig_region_penetration.update_layout(
                title='各区域新品市场渗透率',
                xaxis_title=dict(text="区域", font=dict(size=16)),
                yaxis_title=dict(text="渗透率 (%)", font=dict(size=16)),
                xaxis_tickfont=dict(size=14),
                yaxis_tickfont=dict(size=14),
                margin=dict(t=60, b=80, l=80, r=60),
                plot_bgcolor='rgba(0,0,0,0)',
                barmode='group',
                showlegend=False
            )

            # 确保Y轴有足够空间显示数据标签
            fig_region_penetration.update_yaxes(
                range=[0, region_penetration['渗透率'].max() * 1.2]
            )

            st.plotly_chart(fig_region_penetration, use_container_width=True)



            # 渗透率和销售额关系
            st.markdown('<div class="sub-header section-gap">渗透率与销售额的关系</div>', unsafe_allow_html=True)

            # 计算每个区域的新品销售额
            region_new_sales = filtered_new_products_df.groupby('所属区域')['销售额'].sum().reset_index()
            region_new_sales.columns = ['所属区域', '新品销售额']

            # 合并渗透率和销售额数据
            region_analysis = region_penetration.merge(region_new_sales, on='所属区域', how='left')
            region_analysis['新品销售额'] = region_analysis['新品销售额'].fillna(0)

            # 改进气泡图代码
            fig_bubble = px.scatter(
                region_analysis,
                x='渗透率',
                y='新品销售额',
                size='客户总数',
                size_max=25,  # 限制最大气泡尺寸
                color='所属区域',
                hover_name='所属区域',
                text='所属区域',  # 添加文本标签
                title='区域渗透率与新品销售额关系',
                labels={
                    '渗透率': '渗透率 (%)',
                    '新品销售额': '新品销售额 (元)',
                    '客户总数': '客户总数'
                },
                height=500
            )

            # 使每个气泡都可见且不完全重叠
            fig_bubble.update_traces(
                textposition='middle center',  # 文本位于气泡中心
                textfont=dict(size=12, color='black', family="Arial, sans-serif"),
                marker=dict(
                    line=dict(width=1, color='DarkSlateGrey'),  # 添加气泡边框
                    opacity=0.7  # 增加透明度以便看到重叠部分
                ),
                mode='markers+text'  # 同时显示标记和文本
            )

            # 确保显示所有区域标签
            for i, row in region_analysis.iterrows():
                fig_bubble.add_annotation(
                    x=row['渗透率'],
                    y=row['新品销售额'],
                    text=row['所属区域'],
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1,
                    arrowwidth=2,
                    arrowcolor="#636363",
                    ax=0,
                    ay=-40,
                    font=dict(size=14, color='black')
                )

            # 改进坐标轴和网格
            fig_bubble.update_layout(
                xaxis=dict(showgrid=True, gridcolor='lightgray', dtick=10),
                yaxis=dict(showgrid=True, gridcolor='lightgray', tickprefix='¥', tickformat=','),
                plot_bgcolor='white'
            )

            st.plotly_chart(fig_bubble, use_container_width=True)
        else:
            st.warning("请在侧边栏选择至少一个区域以查看区域渗透率分析。")

        # 渗透率趋势分析（如果有时间数据）
        if '发运月份' in filtered_df.columns:
            st.markdown('<div class="sub-header section-gap">新品渗透率趋势</div>', unsafe_allow_html=True)

            try:
                # 确保发运月份是日期类型
                filtered_df['发运月份'] = pd.to_datetime(filtered_df['发运月份'])
                filtered_new_products_df['发运月份'] = pd.to_datetime(filtered_new_products_df['发运月份'])

                # 按月分组
                monthly_customers = filtered_df.groupby(pd.Grouper(key='发运月份', freq='M'))[
                    '客户简称'].nunique().reset_index()
                monthly_customers.columns = ['月份', '客户总数']

                monthly_new_customers = filtered_new_products_df.groupby(pd.Grouper(key='发运月份', freq='M'))[
                    '客户简称'].nunique().reset_index()
                monthly_new_customers.columns = ['月份', '购买新品客户数']

                # 合并月度数据
                monthly_penetration = monthly_customers.merge(monthly_new_customers, on='月份', how='left')
                monthly_penetration['购买新品客户数'] = monthly_penetration['购买新品客户数'].fillna(0)
                monthly_penetration['渗透率'] = (
                        monthly_penetration['购买新品客户数'] / monthly_penetration['客户总数'] * 100).round(2)
                monthly_penetration['月份_str'] = monthly_penetration['月份'].dt.strftime('%Y-%m')

                # 创建趋势线图
                fig_trend = px.line(
                    monthly_penetration,
                    x='月份',
                    y='渗透率',
                    markers=True,
                    title='新品渗透率月度趋势',
                    labels={'渗透率': '渗透率 (%)', '月份': '月份'},
                    height=500
                )
                # 添加数据标签
                fig_trend.update_traces(
                    text=[f"{x:.1f}%" for x in monthly_penetration['渗透率']],
                    textposition='top center',
                    textfont=dict(size=14)
                )
                fig_trend.update_layout(
                    xaxis_title=dict(text="月份", font=dict(size=16)),
                    yaxis_title=dict(text="渗透率 (%)", font=dict(size=16)),
                    xaxis_tickfont=dict(size=14),
                    yaxis_tickfont=dict(size=14),
                    margin=dict(t=60, b=80, l=80, r=60),
                    plot_bgcolor='rgba(0,0,0,0)'
                )

                st.plotly_chart(fig_trend, use_container_width=True)
            except:
                st.warning("无法处理月份数据进行趋势分析。请确保发运月份格式正确。")
    else:
        st.warning("当前筛选条件下没有数据。请调整筛选条件。")

# 底部下载区域
st.markdown("---")
st.markdown('<div class="sub-header"> 📊 导出分析结果</div>', unsafe_allow_html=True)


# 创建Excel报告
@st.cache_data
def generate_excel_report(df, new_products_df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')

    # 销售概览表
    df.to_excel(writer, sheet_name='销售数据总览', index=False)

    # 新品分析表
    new_products_df.to_excel(writer, sheet_name='新品销售数据', index=False)

    # 区域销售汇总
    region_summary = df.groupby('所属区域').agg({
        '销售额': 'sum',
        '客户简称': pd.Series.nunique,
        '产品代码': pd.Series.nunique,
        '数量（箱）': 'sum'
    }).reset_index()
    region_summary.columns = ['区域', '销售额', '客户数', '产品数', '销售数量']
    region_summary.to_excel(writer, sheet_name='区域销售汇总', index=False)

    # 产品销售汇总
    product_summary = df.groupby(['产品代码', '简化产品名称']).agg({
        '销售额': 'sum',
        '客户简称': pd.Series.nunique,
        '数量（箱）': 'sum'
    }).sort_values('销售额', ascending=False).reset_index()
    product_summary.columns = ['产品代码', '产品名称', '销售额', '购买客户数', '销售数量']
    product_summary.to_excel(writer, sheet_name='产品销售汇总', index=False)

    # 保存Excel
    writer.close()

    return output.getvalue()


excel_report = generate_excel_report(filtered_df, filtered_new_products_df)

# 下载按钮
st.markdown('<div class="download-button">', unsafe_allow_html=True)
st.download_button(
    label="下载Excel分析报告",
    data=excel_report,
    file_name="销售数据分析报告.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
st.markdown('</div>', unsafe_allow_html=True)

# 底部注释
st.markdown("""
<div style="text-align: center; margin-top: 30px; color: #666;">
    <p>销售数据分析仪表盘 © 2025</p>
</div>
""", unsafe_allow_html=True)