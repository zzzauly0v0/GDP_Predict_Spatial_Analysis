<template>
<div class="analysis-container">
<el-container class="full-height">
<div class="title-section">
  <h1 class="main-title">人口经济耦合协调度分析平台</h1>
</div>

<el-header class="header">
  <div class="header-content">
    <div class="header-status">
      <el-card class="status-card">
        <div class="status-content">
          <div class="status-item">
            <div class="status-label">当前年份:</div>
            <div class="status-value">{{ currentYear }}</div>
          </div>
          <div class="status-item">
            <div class="status-label">数据状态:</div>
            <el-tag :type="dataStatus.type">{{ dataStatus.status }}</el-tag>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</el-header>

<el-main class="main-content">
  <div class="container">
    <el-row :gutter="20" class="mb-4">
      <el-col :span="24">
        <el-card class="year-controls">
          <el-row :gutter="20" align="middle">
            <el-col :md="16">
              <h5 class="mb-3">选择分析年份 (2005-2024)</h5>
              <div class="year-buttons mb-3">
                <el-button
                  v-for="year in yearsRange"
                  :key="year"
                  :type="year == currentYear ? 'primary' : 'default'"
                  size="small"
                  @click="loadCouplingData(year.toString())"
                  class="year-btn"
                >
                  {{ year }}
                </el-button>
              </div>
              <div class="quick-select">
                <el-space :size="12" wrap>
                  <span>快速选择:</span>
                  <el-select v-model="selectedYearToLoad" style="width: 120px;">
                    <el-option
                      v-for="year in yearsRange"
                      :key="year"
                      :label="`${year}年`"
                      :value="year"
                    />
                  </el-select>
                  <el-button 
                    type="primary" 
                    @click="loadSelectedCouplingYear"
                    :loading="loading.couplingSpinner"
                  >
                    <el-icon class="is-loading" v-if="loading.couplingSpinner">
                      <Loading />
                    </el-icon>
                    加载数据
                  </el-button>
                </el-space>
              </div>
            </el-col>
            <el-col :md="8" class="text-right">
            
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>

    <!-- 耦合协调度分析内容 -->
    <div class="coupling-section">
      <el-row :gutter="20">
        <el-col :lg="12">
          <!-- 地图 -->
          <el-card class="stats-card">
            <template #header>
              <span>耦合协调度空间分布 <small class="text-muted">({{ currentYear }}年)</small></span>
            </template>
            <div id="couplingMap" class="map-container">
              <div v-if="loading.couplingMapLoading" class="loading">
                <el-icon class="is-loading"><Loading /></el-icon>
                <p class="mt-2">地图加载中...</p>
              </div>
            </div>
          </el-card>

          <el-card class="stats-card">
            <template #header>
              <span>地区协调度完整排名 <small class="text-muted">({{ currentYear }}年)</small></span>
            </template>
            <div class="table-container">
              <el-table 
                :data="couplingRegionsData" 
                height="400"
                v-loading="loading.regionsLoading"
                style="width: 100%"
              >
                <el-table-column label="排名" width="80">
                  <template #default="{$index}">
                    <span class="fw-bold">{{ $index + 1 }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="name" label="地区" />
                <el-table-column label="协调度" width="200">
                  <template #default="{ row }">
                    <div class="coordination-progress">
                      <span class="score" :class="getScoreColorClass(row.coordination_degree)">
                        {{ row.coordination_degree.toFixed(3) }}
                      </span>
                      <el-progress 
                        :percentage="Math.min(row.coordination_degree * 100, 100)"
                        :color="getProgressColor(row.coordination_degree)"
                        :show-text="false"
                      />
                    </div>
                  </template>
                </el-table-column>
                <el-table-column label="类型" width="120">
                  <template #default="{ row }">
                    <el-tag :type="getDevelopmentTypeTagType(row.development_type)" size="small">
                      {{ row.development_type }}
                    </el-tag>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </el-card>
        </el-col>

        <el-col :lg="12">
          <!-- 统计信息 -->
          <el-card class="stats-card">
            <template #header>
              <span>年度分析概览 <small class="text-muted">({{ currentYear }}年)</small></span>
            </template>
            <div>
              <div v-if="loading.statsLoading" class="loading">
                <el-icon class="is-loading"><Loading /></el-icon>
                <span>数据加载中...</span>
              </div>
              <div v-else>
                <el-row :gutter="16">
                  <el-col :span="12">
                    <div class="stat-item">
                      <div class="stat-label">分析年份:</div>
                      <div class="stat-value">{{ currentYear }}年</div>
                    </div>
                    <div class="stat-item">
                      <div class="stat-label">分析地区:</div>
                      <div class="stat-value">{{ couplingStats.total_regions }} 个</div>
                    </div>
                  </el-col>
                  <el-col :span="12">
                    <div class="stat-item">
                      <div class="stat-label">平均协调度:</div>
                      <div class="stat-value" :class="getScoreColorClass(couplingStats.average_coordination)">
                        {{ couplingStats.average_coordination.toFixed(3) }}
                      </div>
                    </div>
                  </el-col>
                </el-row>
                <el-divider />
                <div class="stats-summary">
                  <div class="summary-item">
                    <span class="label">协调度范围:</span>
                    <span>{{ couplingStats.coordination_range.min.toFixed(3) }} - {{ couplingStats.coordination_range.max.toFixed(3) }}</span>
                  </div>
                  <div class="summary-item">
                    <span class="label">协调等级分布:</span>
                    <el-space wrap>
                      <el-tag
                        v-for="(count, level) in couplingStats.level_distribution"
                        :key="level"
                        :type="getLevelTagType(level)"
                        size="small"
                      >
                        {{ level }}: {{ count }}
                      </el-tag>
                    </el-space>
                  </div>
                </div>
              </div>
            </div>
          </el-card>

          <!-- 地区详情 -->
          <el-card class="stats-card">
            <template #header>
              <span>地区详情</span>
            </template>
            <div class="region-info">
              <el-empty v-if="!selectedCouplingRegion" description="点击地图区域查看详情" :image-size="80" />
              <div v-else :class="['region-detail', getRegionCoordinationClass(selectedCouplingRegion.coordination_degree)]">
                <h6>{{ selectedCouplingRegion.region }} ({{ currentYear }}年)</h6>
                <el-divider />
                <div class="region-detail-content">
                  <p><strong>协调度:</strong> {{ selectedCouplingRegion.coordination_degree.toFixed(3) }}</p>
                  <p><strong>协调等级:</strong> {{ selectedCouplingRegion.coordination_level }}</p>
                  <p><strong>发展类型:</strong> {{ selectedCouplingRegion.development_type }}</p>
                  <p><strong>人口数量:</strong> {{ selectedCouplingRegion.population.toLocaleString() }} 万人</p>
                  <p><strong>GDP:</strong> {{ selectedCouplingRegion.gdp.toLocaleString() }} 亿元</p>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

    </div>
  </div>
</el-main>
</el-container>
</div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, onUnmounted } from 'vue';
import {
ElContainer,
ElHeader,
ElMain,
ElCard,
ElButton,
ElRow,
ElCol,
ElSelect,
ElOption,
ElSpace,
ElTag,
ElEmpty,
ElDivider,
ElTable,
ElTableColumn,
ElProgress,
ElIcon
} from 'element-plus';
import { Loading } from '@element-plus/icons-vue';

// 引入OpenLayers
import Map from 'ol/Map';
import View from 'ol/View';
import TileLayer from 'ol/layer/Tile';
import VectorLayer from 'ol/layer/Vector';
import VectorSource from 'ol/source/Vector';
import TileWMS from 'ol/source/TileWMS';
import XYZ from 'ol/source/XYZ';
import { fromLonLat, toLonLat } from 'ol/proj';
import { Style, Fill, Stroke, Text } from 'ol/style';
import GeoJSON from 'ol/format/GeoJSON';
import { defaults as defaultControls, Zoom } from 'ol/control';
import Overlay from 'ol/Overlay';

// 配置
const API_BASE_URL = 'http://localhost:5000/api';
const START_YEAR = 2005;
const END_YEAR = 2024;

// 状态管理
const currentYear = ref(END_YEAR.toString());
const selectedYearToLoad = ref(END_YEAR.toString());
const loading = reactive({
couplingSpinner: false,
couplingMapLoading: false,
statsLoading: false,
regionsLoading: false,
});
const dataStatus = reactive({
status: '就绪',
type: 'success'
});

// 数据存储
const couplingGeojsonData = ref(null);
const couplingRegionsData = ref([]);
const couplingStats = ref({
average_coordination: 0,
total_regions: 0,
coordination_range: { min: 0, max: 0 },
level_distribution: {}
});

// 选中区域
const selectedCouplingRegion = ref(null);

// OpenLayers地图实例
let couplingMapInstance = null;
let vectorSource = null;
let vectorLayer = null;
let popupOverlay = null;

// 计算属性
const yearsRange = computed(() => {
const years = [];
for (let year = END_YEAR; year >= START_YEAR; year--) {
years.push(year);
}
return years;
});

//耦合协调度分析函数
const loadCouplingData = async (year) => {
currentYear.value = year;
setDataStatus('加载中...', 'warning');
loading.couplingSpinner = true;
loading.couplingMapLoading = true;
loading.statsLoading = true;
loading.regionsLoading = true;
selectedCouplingRegion.value = null;

try {
    const [dataResponse, regionsResponse] = await Promise.all([
        fetch(`${API_BASE_URL}/data?year=${year}`),
        fetch(`${API_BASE_URL}/regions?year=${year}`)
    ]);

    if (!dataResponse.ok || !regionsResponse.ok) throw new Error('数据请求失败');

    const data = await dataResponse.json();
    const regionsDataResponse = await regionsResponse.json();

    if (data.success && regionsDataResponse.success) {
        couplingGeojsonData.value = data.geojson;
        couplingRegionsData.value = regionsDataResponse.regions;
        updateCouplingStatistics(data.statistics);
        updateCouplingMap();

        setDataStatus('加载完成', 'success');
    } else {
        throw new Error('数据加载失败: ' + (data.message || regionsDataResponse.message));
    }

} catch (error) {
    console.error('耦合协调度数据加载失败:', error);
    setDataStatus('加载失败', 'danger');
    couplingRegionsData.value = [];
    updateCouplingStatistics({ 
        average_coordination: 0, 
        total_regions: 0, 
        coordination_range: { min: 0, max: 0 }, 
        level_distribution: {} 
    });
} finally {
    loading.couplingSpinner = false;
    loading.couplingMapLoading = false;
    loading.statsLoading = false;
    loading.regionsLoading = false;
}
};

const loadSelectedCouplingYear = () => {
loadCouplingData(selectedYearToLoad.value);
};

// OpenLayers地图相关函数
const initCouplingMap = () => {
  if (couplingMapInstance) {
    couplingMapInstance.setTarget(null);
    couplingMapInstance = null;
  }

  // 天地图底图
  const tianDiTuLayer = new TileLayer({
    source: new XYZ({
      url: 'http://t0.tianditu.gov.cn/vec_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=vec&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=您的天地图密钥',
      wrapX: false
    })
  });

  // GeoServer WMS图层（省界）
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

  // 矢量图层用于显示耦合协调度数据
  vectorSource = new VectorSource();
  vectorLayer = new VectorLayer({
    source: vectorSource,
    style: getCouplingStyle
  });

  // 创建地图实例
  couplingMapInstance = new Map({
    target: 'couplingMap',
    layers: [tianDiTuLayer, shengfenLayer, vectorLayer],
    view: new View({
      center: fromLonLat([103.16, 26.25]),
      zoom: 4,
      projection: 'EPSG:3857',
    }),
    controls: defaultControls().extend([
      new Zoom()
    ])
  });

  // 创建弹出窗口
  popupOverlay = new Overlay({
    element: document.createElement('div'),
    positioning: 'bottom-center',
    stopEvent: false
  });
  couplingMapInstance.addOverlay(popupOverlay);

  // 添加点击事件
  couplingMapInstance.on('click', handleMapClick);
  couplingMapInstance.on('pointermove', handleMapPointerMove);
};

const updateCouplingMap = () => {
  if (!couplingMapInstance) initCouplingMap();
  updateCouplingMapLayer();
};

const updateCouplingMapLayer = () => {
  if (!vectorSource || !couplingGeojsonData.value) return;

  vectorSource.clear();

  if (couplingGeojsonData.value && couplingGeojsonData.value.features) {
    const features = new GeoJSON().readFeatures(couplingGeojsonData.value, {
      featureProjection: 'EPSG:3857'
    });

    features.forEach(feature => {
      const properties = feature.getProperties();
      feature.setProperties(properties);
    });

    vectorSource.addFeatures(features);
    
    // 适配视图到数据范围
    if (features.length > 0) {
      const extent = vectorSource.getExtent();
      couplingMapInstance.getView().fit(extent, {
        padding: [50, 50, 50, 50],
        duration: 1000
      });
    }
  }
};

// 获取样式函数
const getCouplingStyle = (feature) => {
  const coordination = feature.get('coordination_degree');
  let color = '#ff4444';
  
  if (coordination >= 0.8) color = '#00C851';
  else if (coordination >= 0.7) color = '#7fff00';
  else if (coordination >= 0.6) color = '#ffbb33';
  else if (coordination >= 0.5) color = '#ff8800';
  else if (coordination >= 0.3) color = '#ff6b6b';

  return new Style({
    fill: new Fill({
      color: color + 'B3' // 添加透明度
    }),
    stroke: new Stroke({
      color: 'white',
      width: 2
    })
  });
};

// 地图交互处理函数
const handleMapClick = (event) => {
  const feature = couplingMapInstance.forEachFeatureAtPixel(event.pixel, (feature) => {
    return feature;
  });

  if (feature) {
    const properties = feature.getProperties();
    selectedCouplingRegion.value = properties;
    
    // 显示弹出窗口
    showPopup(event.coordinate, properties);
  } else {
    popupOverlay.setPosition(undefined);
  }
};

const handleMapPointerMove = (event) => {
  const pixel = couplingMapInstance.getEventPixel(event.originalEvent);
  const hit = couplingMapInstance.hasFeatureAtPixel(pixel);
  couplingMapInstance.getTargetElement().style.cursor = hit ? 'pointer' : '';
};

const showPopup = (coordinate, properties) => {
  const popupElement = popupOverlay.getElement();
  popupElement.innerHTML = `
    <div class="ol-popup">
      <div class="popup-content">
        <h6>${properties.region}</h6>
        <p><strong>协调度:</strong> ${properties.coordination_degree.toFixed(3)}</p>
        <p><strong>等级:</strong> ${properties.coordination_level}</p>
        <p><strong>类型:</strong> ${properties.development_type}</p>
        <p><strong>人口:</strong> ${properties.population.toLocaleString()} 万人</p>
        <p><strong>GDP:</strong> ${properties.gdp.toLocaleString()} 亿元</p>
      </div>
    </div>
  `;
  popupOverlay.setPosition(coordinate);
};

//图表相关函数 
const updateCouplingStatistics = (stats) => {
couplingStats.value = {
average_coordination: stats.average_coordination || 0,
total_regions: stats.total_regions || 0,
coordination_range: stats.coordination_range || { min: 0, max: 0 },
level_distribution: stats.level_distribution || {}
};
};

//样式辅助函数
const setDataStatus = (status, type = 'success') => {
dataStatus.status = status;
dataStatus.type = type;
};

const getScoreColorClass = (score) => {
if (score >= 0.7) return 'text-success';
if (score >= 0.6) return 'text-warning';
if (score >= 0.5) return 'text-orange';
return 'text-danger';
};

const getLevelTagType = (level) => {
const types = {
'优质协调': 'success',
'中级协调': 'info',
'初级协调': 'warning',
'勉强协调': 'warning',
'中度失调': 'danger',
'严重失调': 'danger'
};
return types[level] || 'info';
};

const getProgressColor = (score) => {
if (score >= 0.8) return '#67c23a';
if (score >= 0.6) return '#e6a23c';
if (score >= 0.4) return '#f56c6c';
return '#909399';
};

const getDevelopmentTypeTagType = (type) => {
const types = {
'协调发展': 'success',
'转型发展': 'warning',
'滞后发展': 'danger'
};
return types[type] || 'info';
};

const getRegionCoordinationClass = (score) => {
if (score >= 0.6) return 'coordination-high';
if (score >= 0.4) return 'coordination-medium';
return 'coordination-low';
};

//生命周期钩子
onMounted(() => {
// 首次加载耦合协调度数据
loadCouplingData(currentYear.value);
});

onUnmounted(() => {
if (couplingMapInstance) {
  couplingMapInstance.setTarget(null);
}
});
</script>

<style scoped>
.analysis-container {
font-family: 'Microsoft YaHei', sans-serif;
background-color: #f8f9fa;
height: 100vh;
display: flex;
flex-direction: column;
overflow: hidden;
}

.full-height {
height: 100%;
}

/* 标题部分 */
.title-section {
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
color: white;
padding: 2rem 0;
text-align: center;
box-shadow: 0 4px 12px rgba(0,0,0,0.15);
position: relative;
z-index: 1001;
}

.main-title {
font-weight: 400;
font-size: 2.5rem;
margin: 0;
letter-spacing: 2px;
text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}

:deep(.el-header) {
padding: 0;
flex-shrink: 0;
height: auto !important;
}

.header {
background: white;
color: #333;
padding: 0.5rem 0;
box-shadow: 0 2px 8px rgba(0,0,0,0.1);
z-index: 1000;
position: relative;
height: auto !important;
}

.header-content {
max-width: 1200px;
margin: 0 auto;
padding: 0 20px;
}

.header-status {
display: flex;
justify-content: center;
}

.status-card {
background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
border: none;
box-shadow: 0 2px 4px rgba(0,0,0,0.05);
padding: 0.5rem 1rem;
}

.status-content {
display: flex;
justify-content: center;
align-items: center;
gap: 2rem;
}

.status-item {
text-align: center;
display: flex;
align-items: center;
gap: 0.5rem;
}

.status-label {
font-size: 0.9rem;
color: #6c757d;
font-weight: 500;
}

.status-value {
font-size: 1.1rem;
font-weight: 600;
color: #495057;
}

.main-content {
flex: 1;
overflow-y: auto;
padding: 0;
background-color: #f8f9fa;
}

:deep(.el-main) {
padding: 0;
}

.container {
max-width: 1200px;
margin: 0 auto;
padding: 20px;
}

.year-controls {
background: white;
padding: 1.5rem;
border-radius: 10px;
margin-bottom: 1.5rem;
box-shadow: 0 2px 8px rgba(0,0,0,0.1);
border: 1px solid #e9ecef;
}

.year-buttons {
display: flex;
flex-wrap: wrap;
gap: 0.5rem;
max-height: 120px;
overflow-y: auto;
padding: 5px;
}

.year-btn {
min-width: 60px;
border-radius: 6px;
font-weight: 500;
}

.quick-select {
display: flex;
align-items: center;
gap: 0.5rem;
flex-wrap: wrap;
margin-top: 1rem;
}

.stats-card {
background: white;
border-radius: 10px;
padding: 1.5rem;
margin-bottom: 1.5rem;
box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
border: 1px solid #e9ecef;
transition: all 0.3s ease;
}

.stats-card:hover {
box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
transform: translateY(-2px);
}

:deep(.stats-card .el-card__header) {
border-bottom: 1px solid #e9ecef;
padding: 1rem 1.5rem;
background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
border-radius: 10px 10px 0 0;
}

:deep(.stats-card .el-card__header span) {
font-weight: 600;
color: #495057;
font-size: 1.1rem;
}

.map-container {
height: 500px;
border-radius: 10px;
overflow: hidden;
box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
position: relative;
border: 1px solid #dee2e6;
}

.loading {
text-align: center;
padding: 2rem;
color: #6c757d;
position: absolute;
top: 50%;
left: 50%;
transform: translate(-50%, -50%);
width: 100%;
background: rgba(255, 255, 255, 0.9);
border-radius: 10px;
}

.loading-overlay {
position: absolute;
top: 0;
left: 0;
right: 0;
bottom: 0;
background: rgba(255, 255, 255, 0.8);
display: flex;
justify-content: center;
align-items: center;
z-index: 10;
border-radius: 10px;
color: #6c757d;
}

.stat-item {
margin-bottom: 1rem;
padding: 0.5rem;
background: #f8f9fa;
border-radius: 6px;
}

.stat-label {
font-size: 0.9rem;
color: #6c757d;
margin-bottom: 0.25rem;
font-weight: 500;
}

.stat-value {
font-size: 1.25rem;
font-weight: 600;
color: #495057;
}

.stats-summary {
background: #f8f9fa;
padding: 1rem;
border-radius: 8px;
border-left: 4px solid #667eea;
}

.summary-item {
margin-bottom: 0.75rem;
display: flex;
align-items: center;
gap: 0.5rem;
}

.summary-item .label {
font-weight: 600;
color: #495057;
min-width: 120px;
}

.region-info {
max-height: 300px;
overflow-y: auto;
}

.region-detail {
padding: 1rem;
border-radius: 8px;
border-left: 4px solid;
}

.region-detail-content p {
margin: 0.75rem 0;
padding: 0.5rem;
background: #f8f9fa;
border-radius: 4px;
}

.table-container {
max-height: 400px;
overflow-y: auto;
border-radius: 8px;
border: 1px solid #e9ecef;
}

:deep(.el-table) {
border-radius: 8px;
overflow: hidden;
}

:deep(.el-table th) {
background-color: #f8f9fa !important;
font-weight: 600;
color: #495057;
}

.coordination-progress {
display: flex;
align-items: center;
gap: 0.75rem;
}

.score {
font-weight: 600;
min-width: 60px;
font-size: 0.9rem;
}

:deep(.el-progress-bar) {
flex-grow: 1;
}

.text-right {
text-align: right;
}

.text-center {
text-align: center;
}

.text-muted {
color: #6c757d;
font-weight: 400;
}

.mb-4 {
margin-bottom: 1.5rem !important;
}

.mb-3 {
margin-bottom: 1rem !important;
}

.mt-2 {
margin-top: 0.5rem !important;
}

.mt-4 {
margin-top: 1.5rem !important;
}

/* OpenLayers 弹出窗口样式 */
:deep(.ol-popup) {
background: white;
border-radius: 8px;
padding: 12px;
box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
min-width: 200px;
border: 1px solid #e9ecef;
}

:deep(.popup-content h6) {
margin: 0 0 8px 0;
color: #495057;
font-weight: 600;
}

:deep(.popup-content p) {
margin: 4px 0;
font-size: 0.9rem;
color: #6c757d;
}

:deep(.ol-popup:after) {
content: "";
position: absolute;
top: 100%;
left: 50%;
margin-left: -8px;
border-width: 8px;
border-style: solid;
border-color: white transparent transparent transparent;
}

.map-container {
  background-color: white;
  height: 500px;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  position: relative;
  border: 1px solid #dee2e6;
}

:deep(.ol-viewport) {
  border-radius: 10px;
}

@media (max-width: 1200px) {
.status-content {
    gap: 1rem;
}
}

@media (max-width: 768px) {
.status-content {
    flex-direction: column;
    gap: 0.5rem;
}
}
</style>