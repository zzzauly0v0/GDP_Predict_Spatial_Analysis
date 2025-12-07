<template>
  <div class="map-container">
    <div id="map" class="map"></div>
    
    <!-- 优化后的数据总览卡片 -->
    <el-card class="overview-card" v-if="overviewData">
      <template #header>
        <div class="card-header">
          <span class="card-title">数据总览</span>
          <el-select v-model="selectedOverviewYear" placeholder="选择年份" @change="loadOverviewData" size="small">
            <el-option 
              v-for="year in availableYears" 
              :key="year" 
              :label="`${year}年`" 
              :value="year"
            />
          </el-select>
        </div>
      </template>
      <div class="overview-content">
        <div class="overview-item" v-for="item in overviewData" :key="item.type">
          <div class="overview-icon" :class="getOverviewIconClass(item.type)">
            <el-icon v-if="item.type === 'gdp'"><PieChart /></el-icon>
            <el-icon v-if="item.type === 'population'"><User /></el-icon>
            <el-icon v-if="item.type === 'financial'"><Money /></el-icon>
            <el-icon v-if="item.type === 'consumer'"><ShoppingCart /></el-icon>
          </div>
          <div class="overview-info">
            <div class="overview-label">{{ item.label }}</div>
            <div class="overview-value">{{ item.value }}{{ item.unit }}</div>
          </div>
          <div class="overview-change" :class="getChangeClass(item.change)">
            <span class="change-icon"></span>
            {{ item.change > 0 ? '+' : '' }}{{ item.change }}%
          </div>
        </div>
      </div>
    </el-card>
    
    <!-- 排行卡片 -->
    <el-card class="ranking-card" v-if="rankingData">
      <template #header>
        <div class="card-header">
          <span class="card-title">数据排行</span>
          <div class="ranking-controls">
            <el-select v-model="selectedRankingYear" placeholder="选择年份" @change="loadRankingData" size="small">
              <el-option 
                v-for="year in availableYears" 
                :key="year" 
                :label="`${year}年`" 
                :value="year"
              />
            </el-select>
            <el-select v-model="selectedRankingType" placeholder="数据类型" @change="loadRankingData" size="small">
              <el-option label="GDP" value="gdp" />
              <el-option label="人口" value="population" />
              <el-option label="财政支出" value="financial" />
              <el-option label="消费品零售额" value="consumer" />
            </el-select>
          </div>
        </div>
      </template>
      <div class="ranking-content">
        <div 
          class="ranking-item" 
          v-for="(item, index) in rankingData" 
          :key="item.region"
          :class="getRankingClass(index)"
        >
          <div class="ranking-rank">
            <span class="rank-number">{{ index + 1 }}</span>
          </div>
          <div class="ranking-info">
            <div class="ranking-region">{{ item.region }}</div>
            <div class="ranking-value">{{ item.value }}{{ rankingUnit }}</div>
          </div>
          <div class="ranking-change" :class="getChangeClass(item.change)">
            <span class="change-icon"></span>
            {{ item.change > 0 ? '+' : '' }}{{ item.change }}%
          </div>
        </div>
      </div>
    </el-card>
    
    <!-- Element Plus 弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="800px"
      :before-close="handleClose"
    >
      <div v-if="featureInfo" class="province-info">
        <!-- 基本信息 -->
        <el-descriptions :column="2" border>
          <el-descriptions-item label="省份名称">
            <el-tag type="primary">{{ featureInfo.NAME || '未知' }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="行政区划代码">
            {{ featureInfo.ADCODE99 || '未知' }}
          </el-descriptions-item>
        </el-descriptions>
        
        <!-- 数据选择器 -->
        <div class="data-selector">
          <el-select v-model="selectedDataType" placeholder="选择数据类型" @change="handleDataTypeChange">
            <el-option label="GDP数据" value="gdp" />
            <el-option label="人口数据" value="population" />
            <el-option label="财政支出数据" value="financial" />
            <el-option label="消费品数据" value="consumer" />
            <el-option label="季度数据" value="quarterly" />
            <el-option label="季度指数数据" value="quarterlyIndex" />
          </el-select>
        </div>
        
        <!-- ECharts图表容器 -->
        <div class="chart-container">
          <div ref="chartRef" style="width: 100%; height: 400px;"></div>
        </div>
        
        <!-- 加载状态 -->
        <div v-if="loading" class="loading-container">
          <el-skeleton :rows="5" animated />
        </div>
        
        <!-- 错误信息 -->
        <div v-if="errorMessage" class="error-message">
          <el-alert :title="errorMessage" type="error" show-icon />
        </div>
        
        <!-- 无数据提示 -->
        <div v-if="!loading && !errorMessage && (!chartData || chartData.values.length === 0)" class="no-data">
          <el-alert title="暂无数据" type="info" show-icon />
        </div>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">关闭</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref, nextTick, watch } from 'vue'
import { Map, View } from 'ol'
import TileLayer from 'ol/layer/Tile'
import 'ol/ol.css'
import { fromLonLat } from 'ol/proj'
import TileWMS from 'ol/source/TileWMS'
import XYZ from 'ol/source/XYZ'
import { 
  ElDialog, 
  ElButton, 
  ElDescriptions, 
  ElDescriptionsItem, 
  ElTag, 
  ElSelect, 
  ElOption,
  ElSkeleton,
  ElAlert,
  ElCard,
  ElIcon
} from 'element-plus'
import { PieChart, User, Money, ShoppingCart } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { 
  getPopulationData, 
  getFinancialExpenditureData, 
  getQuarterlyData, 
  getQuarterlyIndexData,
  getAnnualData,
  getConsumerGoodsData 
} from '../api/index'

// 地图实例
const mapInstance = ref<Map | null>(null)
const dialogVisible = ref(false)
const featureInfo = ref<{
  NAME?: string;
  ADCODE99?: number;
} | null>(null)

// 图表相关
const chartRef = ref<HTMLElement>()
let chartInstance: echarts.ECharts | null = null

// 数据相关
const selectedDataType = ref('gdp')
const loading = ref(false)
const errorMessage = ref('')
const chartData = ref<any>({ values: [] })
const dialogTitle = ref('省份经济数据')

// 卡片相关数据
const overviewData = ref<any[]>([])
const rankingData = ref<any[]>([])
const selectedOverviewYear = ref(new Date().getFullYear() - 1) // 默认去年
const selectedRankingYear = ref(new Date().getFullYear() - 1)
const selectedRankingType = ref('gdp')
const availableYears = ref<number[]>([])
const rankingUnit = ref('')

// 存储所有API数据
const allData = ref<{
  population: any[];
  financial: any[];
  consumer: any[];
  gdp: any[];
}>({
  population: [],
  financial: [],
  consumer: [],
  gdp: []
})

// 数据单位映射
const dataUnits = {
  gdp: '亿元',
  population: '万人',
  financial: '亿元',
  consumer: '亿元'
}

// 数据标签映射
const dataLabels = {
  gdp: 'GDP',
  population: '人口',
  financial: '财政支出',
  consumer: '消费品零售额'
}

// API映射
const apiMap = {
  population: getPopulationData,
  financial: getFinancialExpenditureData,
  consumer: getConsumerGoodsData,
  gdp: getAnnualData,
  quarterly: getQuarterlyData,
  quarterlyIndex: getQuarterlyIndexData
}

// 省份名称映射
const provinceNameMap: Record<string, string> = {
  '北京市': '北京',
  '天津市': '天津',
  '上海市': '上海',
  '重庆市': '重庆',
  '内蒙古自治区': '内蒙古',
  '西藏自治区': '西藏',
  '新疆维吾尔自治区': '新疆',
  '广西壮族自治区': '广西',
  '宁夏回族自治区': '宁夏',
  '香港特别行政区': '香港',
  '澳门特别行政区': '澳门'
}

onMounted(() => {
  // 初始化地图
  const tianDiTuLayer = new TileLayer({
    source: new XYZ({
      url: 'http://t{0-7}.tianditu.gov.cn/vec_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=vec&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=91cc78d5c861104952a1fb36c31936eb',
      wrapX: false
    })
  });

  const shengfenLayer = new TileLayer({
    source: new TileWMS({
      url: 'http://localhost:8080/geoserver/gcsj3/wms',
      params: {
        'VERSION': '1.1.1',
        tiled: true,
        STYLES: '',
        LAYERS: 'gcsj3:省界_Project'
      },
      wrapX: false
    })
  });

  mapInstance.value = new Map({
    target: 'map',
    layers: [
      tianDiTuLayer,
      shengfenLayer
    ],
    view: new View({
      center: fromLonLat([103.16, 26.25]),
      zoom: 4,
      projection: 'EPSG:3857',
    }),
    controls: []
  });

  // 添加点击事件监听（原有代码保持不变）
   mapInstance.value.on('singleclick', async (evt) => {
    try {
      const view = mapInstance.value!.getView()
      const source = shengfenLayer.getSource() as TileWMS
      
      // 构造GetFeatureInfo请求URL
      const url = source.getFeatureInfoUrl(
        evt.coordinate,
        view.getResolution()!,
        view.getProjection()!,
        {
          'INFO_FORMAT': 'application/json',
          'FEATURE_COUNT': 1
        }
      )
      
      if (url) {
        const response = await fetch(url)
        const data = await response.json()
        
        if (data.features && data.features.length > 0) {
          const properties = data.features[0].properties
          featureInfo.value = {
            NAME: properties.NAME,
            ADCODE99: properties.ADCODE99
          }
          
          dialogTitle.value = properties.NAME ? `${properties.NAME} - 经济数据` : '经济数据'
          dialogVisible.value = true
          
          // 显示弹窗后加载数据
          nextTick(() => {
            loadChartData()
          })
        }
      }
    } catch (error) {
      console.error('获取要素信息失败:', error)
      errorMessage.value = '获取省份信息失败'
    }
  })


  const handleResize = () => {
    mapInstance.value?.updateSize()
  }
  window.addEventListener('resize', handleResize)
  
  // 新增：加载数据并初始化卡片
  loadAllData()
})

// 新增：加载所有数据
const loadAllData = async () => {
  try {
    // 并行加载所有数据
    const [populationRes, financialRes, consumerRes, gdpRes] = await Promise.all([
      getPopulationData(),
      getFinancialExpenditureData(),
      getConsumerGoodsData(),
      getAnnualData()
    ])
    
    // 存储数据
    allData.value.population = populationRes.data?.data || []
    allData.value.financial = financialRes.data?.data || []
    allData.value.consumer = consumerRes.data?.data || []
    allData.value.gdp = gdpRes.data?.data || []
    
    // 提取可用年份
    extractAvailableYears()
    
    // 初始化卡片数据
    loadOverviewData()
    loadRankingData()
    
  } catch (error) {
    console.error('加载数据失败:', error)
  }
}

// 新增：提取可用年份
const extractAvailableYears = () => {
  const years = new Set<number>()
  
  // 从所有数据中提取年份
  Object.values(allData.value).forEach(dataArray => {
    if (Array.isArray(dataArray)) {
      dataArray.forEach(item => {
        Object.keys(item).forEach(key => {
          const yearMatch = key.match(/^(\d{4})年$/)
          if (yearMatch) {
            years.add(parseInt(yearMatch[1]))
          }
        })
      })
    }
  })
  
  availableYears.value = Array.from(years).sort((a, b) => b - a)
  
  // 设置默认年份
  if (availableYears.value.length > 0) {
    selectedOverviewYear.value = availableYears.value[0]
    selectedRankingYear.value = availableYears.value[0]
  }
}

// 加载总览数据
const loadOverviewData = () => {
  const year = selectedOverviewYear.value
  const yearStr = `${year}年`
  
  overviewData.value = [
    { type: 'gdp', label: '全国GDP', unit: '亿元' },
    { type: 'population', label: '全国人口', unit: '万人' },
    { type: 'financial', label: '全国财政支出', unit: '亿元' },
    { type: 'consumer', label: '全国消费品零售额', unit: '亿元' }
  ].map(item => {
    const dataArray = allData.value[item.type]
    if (!Array.isArray(dataArray)) {
      return { ...item, value: 0, change: 0 }
    }
    
    // 计算当前年份总和
    const currentYearTotal = dataArray.reduce((sum, province) => {
      const value = parseFloat(province[yearStr]) || 0
      return sum + value
    }, 0)
    
    // 计算去年总和（用于计算增长率）
    const lastYearStr = `${year - 1}年`
    const lastYearTotal = dataArray.reduce((sum, province) => {
      const value = parseFloat(province[lastYearStr]) || 0
      return sum + value
    }, 0)
    
    const change = lastYearTotal > 0 ? 
      ((currentYearTotal - lastYearTotal) / lastYearTotal * 100) : 0
    
    return {
      ...item,
      value: currentYearTotal.toFixed(2),
      change: change.toFixed(2)
    }
  })
}

// 加载排行数据
const loadRankingData = () => {
  const year = selectedRankingYear.value
  const yearStr = `${year}年`
  const type = selectedRankingType.value
  
  const dataArray = allData.value[type]
  if (!Array.isArray(dataArray)) {
    rankingData.value = []
    return
  }
  
    // 设置单位
  rankingUnit.value = dataUnits[type as keyof typeof dataUnits] || ''
  
  // 处理数据：获取每个省份的当前年份数据和增长率
  const processedData = dataArray.map(province => {
    const currentValue = parseFloat(province[yearStr]) || 0
    const lastYearStr = `${year - 1}年`
    const lastValue = parseFloat(province[lastYearStr]) || 0
    
    const change = lastValue > 0 ? 
      ((currentValue - lastValue) / lastValue * 100) : 0
    
    return {
      region: province.地区,
      value: currentValue.toFixed(2),
      change: change.toFixed(2)
    }
  })
  
  // 按值排序
  rankingData.value = processedData
    .sort((a, b) => parseFloat(b.value) - parseFloat(a.value))
}
// 获取变化样式类
const getChangeClass = (change: number) => {
  return change > 0 ? 'positive' : change < 0 ? 'negative' : 'neutral'
}

// 获取排行样式类
const getRankingClass = (index: number) => {
  if (index === 0) return 'rank-first'
  if (index === 1) return 'rank-second'
  if (index === 2) return 'rank-third'
  return ''
}

//获取总览卡片图标样式类
const getOverviewIconClass = (type: string) => {
  const classes = {
    gdp: 'icon-gdp',
    population: 'icon-population',
    financial: 'icon-financial',
    consumer: 'icon-consumer'
  }
  return classes[type as keyof typeof classes] || ''
}
// 加载图表数据
const loadChartData = async () => {
  if (!featureInfo.value) return
  
  loading.value = true
  errorMessage.value = ''
  chartData.value = { values: [] }
  
  try {
    const apiFunction = apiMap[selectedDataType.value as keyof typeof apiMap]
    const response = await apiFunction()
    
    console.log('API响应:', response)
    
    // 处理数据
    chartData.value = processChartData(response.data, featureInfo.value)
    
    console.log('处理后的图表数据:', chartData.value)
    
    // 渲染图表
    if (chartData.value && chartData.value.values && chartData.value.values.length > 0) {
      nextTick(() => {
        renderChart()
      })
    } else {
      console.warn('没有可用的图表数据')
    }
  } catch (error) {
    console.error('加载图表数据失败:', error)
    errorMessage.value = '加载数据失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

// 处理图表数据 
const processChartData = (apiData: any, provinceInfo: any) => {

  // 支持的API数据结构
  let dataArray = null
  
  if (apiData && apiData.code === 0 && apiData.data) {
    dataArray = apiData.data
  } else if (Array.isArray(apiData)) {
    // 直接返回数组
    dataArray = apiData
  } else {
    console.warn('不支持的API数据结构:', apiData)
    return { values: [] }
  }
  
  if (!Array.isArray(dataArray) || dataArray.length === 0) {
    console.warn('数据数组为空或不是数组')
    return { values: [] }
  }
  
  // 获取省份名称的匹配
  const provinceName = getMatchedProvinceName(provinceInfo.NAME, dataArray)
  if (!provinceName) {
    console.warn(`未找到省份 ${provinceInfo.NAME} 的数据，可用地区:`, dataArray.map((item: any) => item.地区))
    return { values: [] }
  }
  
  // 找到对应省份的数据
  const provinceData = dataArray.find((item: any) => item.地区 === provinceName)
  
  if (!provinceData) {
    console.warn(`未找到省份 ${provinceName} 的具体数据`)
    console.log('所有可用数据键:', Object.keys(dataArray[0] || {}))
    return { values: [] }
  }
  
  console.log('找到的省份数据:', provinceData)
  
  // 根据数据类型处理不同的时间格式
  if (selectedDataType.value === 'quarterly' || selectedDataType.value === 'quarterlyIndex') {
    return processQuarterlyData(provinceData, provinceInfo)
  } else {
    return processAnnualData(provinceData, provinceInfo)
  }
}

// 处理季度数据 
const processQuarterlyData = (provinceData: any, provinceInfo: any) => {
  const quarters: string[] = []
  const values: number[] = []

  console.log('处理季度数据，可用键:', Object.keys(provinceData))

  // 遍历数据项，提取季度数据
  Object.keys(provinceData).forEach(key => {
    // 匹配格式 
    const match = key.match(/^(\d{4})年(第[一二三四]季度)$/)
    if (match) {
      const year = match[1]
      const quarterChinese = match[2]
      
      // 中文季度转数字
      const quarterMap: { [key: string]: number } = {
        '第一季度': 1,
        '第二季度': 2, 
        '第三季度': 3,
        '第四季度': 4
      }
      
      const quarter = quarterMap[quarterChinese]
      if (quarter) {
        const quarterLabel = `${year}Q${quarter}`
        let value = parseFloat(provinceData[key])
        
        if (!isNaN(value)) {
          quarters.push(quarterLabel)
          values.push(value)
          console.log(`找到季度数据: ${key} -> ${quarterLabel} = ${value}`)
        } else {
          console.warn(`无法解析数值: ${provinceData[key]}`)
        }
      }
    } else if (key.includes('年') && key.includes('季度') && !key.includes('_pk') && key !== '地区') {
      console.log('未匹配的季度键:', key)
    }
  })

  // 按时间排序（年份+季度）
  if (quarters.length > 0) {
    const sortedIndices = quarters.map((_, index) => index)
      .sort((a, b) => {
        const [yearA, quarterA] = quarters[a].split('Q').map(Number)
        const [yearB, quarterB] = quarters[b].split('Q').map(Number)
        return yearA !== yearB ? yearA - yearB : quarterA - quarterB
      })

    const sortedQuarters = sortedIndices.map(i => quarters[i])
    const sortedValues = sortedIndices.map(i => values[i])

    console.log('处理后的季度数据:', { quarters: sortedQuarters, values: sortedValues })

    return {
      quarters: sortedQuarters,
      values: sortedValues,
      provinceName: provinceInfo.NAME,
      isQuarterly: true
    }
  }

  console.warn('未找到任何季度数据')
  return { values: [] }
}

// 处理年度数据
const processAnnualData = (provinceData: any, provinceInfo: any) => {
  const years: number[] = []
  const values: number[] = []

  // 遍历数据项，提取年份数据
  Object.keys(provinceData).forEach(key => {
    // 匹配 "2021年" 格式（排除季度数据）
    const yearMatch = key.match(/^(\d{4})年$/)
    if (yearMatch && !key.includes('季度')) {
      const year = parseInt(yearMatch[1])
      let value = parseFloat(provinceData[key])
      
      if (!isNaN(year) && !isNaN(value)) {
        years.push(year)
        values.push(value)
        console.log(`找到年度数据: ${year}年 = ${value}`)
      }
    }
  })

  // 按年份排序
  if (years.length > 0) {
    const sortedIndices = years.map((_, index) => index)
      .sort((a, b) => years[a] - years[b])

    const sortedYears = sortedIndices.map(i => years[i])
    const sortedValues = sortedIndices.map(i => values[i])

    console.log('处理后的年度数据:', { years: sortedYears, values: sortedValues })

    return {
      years: sortedYears,
      values: sortedValues,
      provinceName: provinceInfo.NAME,
      isQuarterly: false
    }
  }

  console.warn('未找到任何年度数据')
  return { values: [] }
}

// 获取匹配的省份名称
const getMatchedProvinceName = (mapProvinceName: string, apiData: any[]): string | null => {
  if (!mapProvinceName) return null
  
  // 首先尝试直接匹配
  const directMatch = apiData.find(item => item.地区 === mapProvinceName)
  if (directMatch) return mapProvinceName
  
  // 尝试使用名称映射
  const mappedName = provinceNameMap[mapProvinceName]
  if (mappedName) {
    const mappedMatch = apiData.find(item => item.地区 === mappedName)
    if (mappedMatch) return mappedName
  }
  
  // 尝试部分匹配
  for (const item of apiData) {
    if (item.地区 && (item.地区.includes(mapProvinceName) || mapProvinceName.includes(item.地区))) {
      return item.地区
    }
  }
  
  return null
}

// 渲染ECharts图表
const renderChart = () => {
  if (!chartRef.value || !chartData.value || chartData.value.values.length === 0) {
    console.warn('无法渲染图表: 没有有效数据')
    return
  }
  
  // 销毁之前的图表实例
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
  
  // 初始化图表
  chartInstance = echarts.init(chartRef.value)
  
  const isQuarterly = chartData.value.isQuarterly
  const xAxisData = isQuarterly ? chartData.value.quarters : chartData.value.years
  const xAxisName = isQuarterly ? '季度' : '年份'
  
  const option = {
    title: {
      text: `${chartData.value.provinceName} - ${getDataTypeLabel(selectedDataType.value)}`,
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const data = params[0]
        const unit = getDataUnit(selectedDataType.value)
        if (isQuarterly) {
          return `${data.name}<br/>${getDataTypeLabel(selectedDataType.value)}: ${data.value}${unit}`
        } else {
          return `${data.name}年<br/>${getDataTypeLabel(selectedDataType.value)}: ${data.value}${unit}`
        }
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: xAxisData,
      name: xAxisName,
      axisLabel: {
        rotate: isQuarterly ? 45 : 0
      }
    },
    yAxis: {
      type: 'value',
      name: `${getDataTypeLabel(selectedDataType.value)} (${getDataUnit(selectedDataType.value)})`,
      axisLabel: {
        formatter: `{value} ${getDataUnit(selectedDataType.value)}`
      }
    },
    series: [
      {
        name: getDataTypeLabel(selectedDataType.value),
        type: 'line',
        data: chartData.value.values,
        smooth: true,
        lineStyle: {
          width: 3,
          color: '#5470c6'
        },
        itemStyle: {
          color: '#5470c6'
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(84, 112, 198, 0.5)' },
            { offset: 1, color: 'rgba(84, 112, 198, 0.1)' }
          ])
        }
      }
    ],
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100
      },
      {
        type: 'slider',
        start: 0,
        end: 100
      }
    ]
  }
  
  chartInstance.setOption(option)
  
  // 响应窗口大小变化
  const handleChartResize = () => {
    chartInstance?.resize()
  }
  window.addEventListener('resize', handleChartResize)
}

// 获取数据类型标签
const getDataTypeLabel = (type: string) => {
  const labels: { [key: string]: string } = {
    gdp: 'GDP',
    population: '人口',
    financial: '财政支出',
    consumer: '消费品零售额',
    quarterly: '季度数据',
    quarterlyIndex: '季度指数'
  }
  return labels[type] || '数据'
}

// 获取数据单位
const getDataUnit = (type: string) => {
  const units: { [key: string]: string } = {
    gdp: '亿元',
    population: '万人',
    financial: '亿元',
    consumer: '亿元',
    quarterly: '亿元',
    quarterlyIndex: '指数'
  }
  return units[type] || ''
}

// 数据类型变更处理
const handleDataTypeChange = () => {
  loadChartData()
}

// 弹窗关闭处理
const handleClose = (done: () => void) => {
  // 销毁图表实例
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
  done()
}

onUnmounted(() => {
  mapInstance.value?.setTarget(null)
  if (chartInstance) {
    chartInstance.dispose()
  }
})

</script>

<style scoped>
.map-container {
  width: 100%;
  height: 100%;
  position: relative;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

.map {
  width: 100%;
  height: 100%;
  min-height: 600px;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

/* 优化：总览卡片样式 - 增加宽度 */
.overview-card {
  position: absolute;
  top: 20px;
  left: 20px;
  width: 380px; /* 增加宽度 */
  z-index: 1000;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px; /* 增加内边距 */
}

.card-title {
  font-size: 18px; /* 增大字体 */
  font-weight: 600;
  color: #2c3e50;
  display: flex;
  align-items: center;
  white-space: nowrap; /* 防止换行 */
}

.card-title::before {
  content: '';
  display: inline-block;
  width: 4px;
  height: 18px; /* 增加高度 */
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 2px;
  margin-right: 10px; /* 增加间距 */
}

.overview-content {
  margin-top: 8px;
  padding: 0 12px 12px; /* 增加内边距 */
}

.overview-item {
  display: flex;
  align-items: center;
  padding: 14px 12px; /* 增加内边距 */
  border-bottom: 1px solid rgba(240, 240, 240, 0.8);
  transition: all 0.3s ease;
}

.overview-item:hover {
  background: rgba(248, 250, 252, 0.8);
  border-radius: 8px;
  padding-left: 12px;
  padding-right: 12px;
  margin: 0 -12px;
}

.overview-item:last-child {
  border-bottom: none;
}

.overview-icon {
  width: 44px; /* 增加尺寸 */
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 14px; /* 增加间距 */
  font-size: 20px; /* 增大图标 */
  color: white;
}

.icon-gdp {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.icon-population {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.icon-financial {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.icon-consumer {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.overview-info {
  flex: 1;
}

.overview-label {
  font-size: 14px; /* 增大字体 */
  color: #7f8c8d;
  margin-bottom: 4px;
}

.overview-value {
  font-size: 18px; /* 增大字体 */
  font-weight: 600;
  color: #2c3e50;
}

.overview-change {
  font-size: 13px; /* 增大字体 */
  font-weight: 600;
  padding: 6px 10px; /* 增加内边距 */
  border-radius: 12px;
  display: flex;
  align-items: center;
}

.overview-change.positive {
  background: rgba(52, 199, 89, 0.1);
  color: #34c759;
}

.overview-change.negative {
  background: rgba(255, 59, 48, 0.1);
  color: #ff3b30;
}

.overview-change.neutral {
  background: rgba(142, 142, 147, 0.1);
  color: #8e8e93;
}

.change-icon {
  width: 0;
  height: 0;
  border-left: 4px solid transparent;
  border-right: 4px solid transparent;
  margin-right: 6px; /* 增加间距 */
}

.overview-change.positive .change-icon {
  border-bottom: 6px solid #34c759;
}

.overview-change.negative .change-icon {
  border-top: 6px solid #ff3b30;
}

.overview-change.neutral .change-icon {
  border-left: 6px solid #8e8e93;
  border-right: 0;
  border-top: 3px solid transparent;
  border-bottom: 3px solid transparent;
}

/* 优化：排行卡片样式 */
.ranking-card {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 400px; /* 稍微增加宽度以保持平衡 */
  max-height: 500px;
  z-index: 1000;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.ranking-controls {
  display: flex;
  gap: 8px;
}

.ranking-controls .el-select {
  width: 110px;
}

.ranking-content {
  margin-top: 8px;
  max-height: 400px;
  overflow-y: auto;
  padding-right: 4px;
}

.ranking-content::-webkit-scrollbar {
  width: 4px;
}

.ranking-content::-webkit-scrollbar-track {
  background: rgba(240, 240, 240, 0.5);
  border-radius: 2px;
}

.ranking-content::-webkit-scrollbar-thumb {
  background: rgba(200, 200, 200, 0.8);
  border-radius: 2px;
}

.ranking-content::-webkit-scrollbar-thumb:hover {
  background: rgba(150, 150, 150, 0.8);
}

.ranking-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  margin-bottom: 8px;
  border-radius: 12px;
  background: rgba(248, 250, 252, 0.8);
  transition: all 0.3s ease;
  border: 1px solid transparent;
}

.ranking-item:hover {
  background: rgba(255, 255, 255, 1);
  border-color: rgba(226, 232, 240, 0.8);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.ranking-item.rank-first {
  background: linear-gradient(135deg, rgba(255, 215, 0, 0.1) 0%, rgba(255, 193, 61, 0.2) 100%);
  border-left: 4px solid #ffd700;
}

.ranking-item.rank-second {
  background: linear-gradient(135deg, rgba(192, 192, 192, 0.1) 0%, rgba(169, 169, 169, 0.2) 100%);
  border-left: 4px solid #c0c0c0;
}

.ranking-item.rank-third {
  background: linear-gradient(135deg, rgba(205, 127, 50, 0.1) 0%, rgba(210, 180, 140, 0.2) 100%);
  border-left: 4px solid #cd7f32;
}

.ranking-rank {
  width: 32px;
  text-align: center;
}

.rank-number {
  display: inline-flex;
  width: 28px;
  height: 28px;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #64748b;
  color: white;
  font-size: 12px;
  font-weight: 600;
}

.ranking-item.rank-first .rank-number {
  background: linear-gradient(135deg, #ffd700 0%, #ffa500 100%);
  box-shadow: 0 2px 8px rgba(255, 215, 0, 0.3);
}

.ranking-item.rank-second .rank-number {
  background: linear-gradient(135deg, #c0c0c0 0%, #a9a9a9 100%);
  box-shadow: 0 2px 8px rgba(192, 192, 192, 0.3);
}

.ranking-item.rank-third .rank-number {
  background: linear-gradient(135deg, #cd7f32 0%, #d2b48c 100%);
  box-shadow: 0 2px 8px rgba(205, 127, 50, 0.3);
}

.ranking-info {
  flex: 1;
  margin: 0 16px;
}

.ranking-region {
  font-size: 14px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 2px;
}

.ranking-value {
  font-size: 12px;
  color: #64748b;
}

.ranking-change {
  font-size: 12px;
  font-weight: 600;
  padding: 6px 10px;
  border-radius: 12px;
  display: flex;
  align-items: center;
}

.ranking-change.positive {
  background: rgba(52, 199, 89, 0.1);
  color: #34c759;
}

.ranking-change.negative {
  background: rgba(255, 59, 48, 0.1);
  color: #ff3b30;
}

.ranking-change.neutral {
  background: rgba(142, 142, 147, 0.1);
  color: #8e8e93;
}

/* 原有样式保持不变 */
.province-info {
  padding: 10px 0;
}

.data-selector {
  margin: 20px 0;
  display: flex;
  justify-content: center;
}

.chart-container {
  margin-top: 20px;
}

.loading-container {
  margin-top: 20px;
}

.error-message {
  margin-top: 20px;
}

.no-data {
  margin-top: 20px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .map {
    min-height: 400px;
  }
  
  .overview-card,
  .ranking-card {
    position: relative;
    width: calc(100% - 40px);
    margin: 10px 20px;
    top: auto;
    right: auto;
    left: auto;
  }
  
  .ranking-controls {
    flex-direction: column;
    gap: 4px;
  }
  
  .ranking-controls .el-select {
    width: 100%;
  }
}
</style>