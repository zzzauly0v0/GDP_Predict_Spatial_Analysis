<template>
  <div class="spatial-analysis-container">
    <div id="map" ref="mapContainer"></div>
    
    <div class="control-panel">
      <h3 style="margin-bottom: 15px; color: #1890ff;">GDP空间分析系统</h3>
      
      <div class="control-group">
        <label>选择年份：</label>
        <select v-model="currentYear" @change="handleYearChange">
          <option v-for="year in availableYears" :key="year" :value="year">{{ year }}</option>
        </select>
      </div>
      
      <div class="control-group">
        <label>分析类型：</label>
        <select v-model="currentDataType" @change="handleDataTypeChange">
          <option value="gdp">GDP分布图</option>
          <option value="lisa">LISA聚类分析</option>
          <option value="gi">Gi*热点分析</option>
        </select>
      </div>
      
      <div class="control-group">
        <label>颜色方案：</label>
        <select v-model="currentColorScheme" @change="handleColorSchemeChange">
          <option value="default">默认配色</option>
          <option value="redblue">（红）蓝配色</option>
          <option value="green">绿色系</option>
        </select>
      </div>
      
      <button @click="refreshData">刷新数据</button>
      <button @click="resetView" style="margin-top: 10px; background: #52c41a;">重置视图</button>
      
      <div class="control-group" style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #eee;">
        <div class="stats" id="stats-info">
          {{ statsInfo }}
        </div>
      </div>
    </div>
    
    <div class="legend">
      <h4>图例</h4>
      <div id="legend-content"></div>
    </div>
    
    <div class="info-panel" v-show="showInfoPanel">
      <h3>{{ provinceInfo.name }}</h3>
      <div class="stats">
        <div><strong>GDP:</strong> {{ provinceInfo.gdp ? formatNumber(provinceInfo.gdp) + ' 亿元' : 'N/A' }}</div>
        <div v-if="provinceInfo.lisa_type"><strong>LISA聚类:</strong> {{ provinceInfo.lisa_type }}</div>
        <div v-if="provinceInfo.gi_type"><strong>Gi*热点:</strong> {{ provinceInfo.gi_type }}</div>
        <div v-if="provinceInfo.lisa_I"><strong>LISA指数:</strong> {{ provinceInfo.lisa_I.toFixed(3) }}</div>
        <div v-if="provinceInfo.gi_z"><strong>Gi* Z值:</strong> {{ provinceInfo.gi_z.toFixed(3) }}</div>
      </div>
    </div>
    
    <div class="loading" v-show="loading">
      数据加载中...
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import * as turf from '@turf/turf' // 引入 turf.js 
import { 
  getSpatialAnalysisData, 
  getSpatialAvailableYears, 
  getSpatialYearStats, 
  refreshSpatialData 
} from '../api/index'

export default {
  name: 'SpatialAnalysis',
  setup() {
    // 响应式数据
    const mapContainer = ref(null)
    const map = ref(null)
    const currentLayer = ref(null)
    const currentGeoJSON = ref(null)
    const currentYear = ref('')
    const currentDataType = ref('gi')
    const currentColorScheme = ref('default')
    const availableYears = ref([])
    const statsInfo = ref('请选择年份和分析类型')
    const showInfoPanel = ref(false)
    const provinceInfo = ref({})
    const loading = ref(false)
    
    // 存储省份标签图层
    const provinceLabelsLayer = ref(null)
    
    const manualCenters = {
      '河北省': [39.0, 115.5], 
      '内蒙古自治区': [41.0, 110.0], 
      '新疆维吾尔自治区': [42.0, 85.0],
      '陕西省': [35.0, 109.0],
      '甘肃省': [36.0, 104.0],
      '香港': [22.30, 114.17], 
      '澳门': [22.19, 113.54],
      '台湾省': [23.7, 121.0]
    };
    
    // 颜色配置
    const colorSchemes = {
      default: {
        gdp: {
          breaks: [0, 10000, 50000, 100000, 200000],
          colors: ['#fee5d9', '#fcae91', '#fb6a4a', '#de2d26', '#a50f15'],
          labels: ['<1万', '1-5万', '5-10万', '10-20万', '>20万']
        },
        lisa: {
          '高-高聚类': '#d73027',
          '低-低聚类': '#4575b4', 
          '高-低异常': '#fdae61',
          '低-高异常': '#abd9e9'
        },
        gi: {
          '热点': '#d73027',
          '冷点': '#4575b4',
          '不显著': '#cccccc'
        }
      },
      redblue: {
        gdp: {
          breaks: [0, 10000, 50000, 100000, 200000],
          colors: ['#f7fbff', '#c6dbef', '#6baed6', '#2171b5', '#08306b'],
          labels: ['<1万', '1-5万', '5-10万', '10-20万', '>20万']
        },
        lisa: {
          '高-高聚类': '#cb181d',
          '低-低聚类': '#08519c', 
          '高-低异常': '#fb6a4a',
          '低-高异常': '#6baed6'
        },
        gi: {
          '热点': '#cb181d',
          '冷点': '#08519c',
          '不显著': '#f0f0f0'
        }
      },
      green: {
        gdp: {
          breaks: [0, 10000, 50000, 100000, 200000],
          colors: ['#f7fcf5', '#c7e9c0', '#74c476', '#31a354', '#006d2c'],
          labels: ['<1万', '1-5万', '5-10万', '10-20万', '>20万']
        },
        lisa: {
          '高-高聚类': '#238b45',
          '低-低聚类': '#006d2c', 
          '高-低异常': '#74c476',
          '低-高异常': '#bae4b3'
        },
        gi: {
          '热点': '#238b45',
          '冷点': '#006d2c',
          '不显著': '#f0f0f0'
        }
      }
    }

    // 初始化地图
    const initMap = () => {
      if (mapContainer.value) {
        // 设置中国边界限制
        const chinaBounds = L.latLngBounds(
          L.latLng(15, 70),   // 西南角
          L.latLng(55, 140)   // 东北角
        )

        map.value = L.map(mapContainer.value, {
          center: [35, 105],
          zoom: 4,
          minZoom: 3,
          maxZoom: 8,
          zoomControl: false,
          attributionControl: false,
        })

        // 添加自定义缩放控件
        L.control.zoom({
          position: 'topright'
        }).addTo(map.value)
        
        // 点击地图其他地方隐藏信息面板
        map.value.on('click', function(e) {
          if (e.originalEvent && !e.originalEvent.propagatedFromFeature) {
            showInfoPanel.value = false
          }
        })
      }
    }

    // 添加省份名称标签
    const addProvinceLabels = (geojsonData) => {
      // 清除之前的标签
      if (provinceLabelsLayer.value) {
        map.value.removeLayer(provinceLabelsLayer.value)
      }

      const labelLayer = L.layerGroup()
      
      geojsonData.features.forEach(feature => {
        const properties = feature.properties
        const geometry = feature.geometry
        const provinceName = properties.name || properties.region || '未知' // 提取省份名称
        
        // 计算省份中心点，传入省份名称以支持手动覆盖
        const center = calculateProvinceCenter(geometry, provinceName) 
        if (center) {
          // 创建省份标签
          const label = L.divIcon({
            html: `<div class="province-label">${provinceName}</div>`,
            className: 'province-label-container',
            iconSize: [120, 30],
            iconAnchor: [60, 15]
          })
          
          const marker = L.marker(center, {
            icon: label,
            interactive: false // 标签不可点击
          })
          
          labelLayer.addLayer(marker)
        }
      })
      
      labelLayer.addTo(map.value)
      provinceLabelsLayer.value = labelLayer
    }

 
    const calculateProvinceCenter = (geometry, provinceName) => {

      if (provinceName && manualCenters[provinceName]) {
          return manualCenters[provinceName];
      }
      
      // 准备 GeoJSON Feature
      const feature = {
        type: 'Feature',
        geometry: geometry,
        properties: {}
      }
      
      try {
        const centerPoint = turf.pointOfInaccessibility(feature, { tolerance: 0.01 })
        
        // Turf 返回 [经度, 纬度] (lng, lat)
        const coords = centerPoint.geometry.coordinates
        return [coords[1], coords[0]] // Leaflet 需要 [lat, lng]
        
      } catch (e) {
        console.warn(`计算 ${provinceName} 的极点失败，回退到 Centroid:`, e);
        
        try {
            const centerPoint = turf.centroid(feature)
            const coords = centerPoint.geometry.coordinates
            return [coords[1], coords[0]]
        } catch (centroidError) {
            console.error(`${provinceName} 的 Centroid 计算也失败:`, centroidError);
            return null;
        }
      }
    }
    

    // 加载可用年份
    const loadAvailableYears = async () => {
      try {
        const response = await getSpatialAvailableYears()
        const data = response.data
        
        if (data.available_years && data.available_years.length > 0) {
          availableYears.value = data.available_years
          currentYear.value = data.available_years[0]
          loadSpatialData(currentYear.value, currentDataType.value)
        } else {
          statsInfo.value = '无可用数据'
        }
      } catch (error) {
        console.error('加载年份列表失败:', error)
        statsInfo.value = '连接服务器失败'
      }
    }

    // 加载空间数据
    const loadSpatialData = async (year, dataType) => {
      loading.value = true
      let geojsonData = null // ✅ 修复 1: 提升变量作用域
      try {
        const response = await getSpatialAnalysisData(year)
        geojsonData = response.data // ✅ 修复 2: 赋值，而不是重新声明
        
        currentGeoJSON.value = geojsonData

        // 移除现有图层
        if (currentLayer.value) {
          map.value.removeLayer(currentLayer.value)
        }

        // 获取颜色方案
        const colors = colorSchemes[currentColorScheme.value] || colorSchemes.default

        // 添加新图层
        currentLayer.value = L.geoJSON(geojsonData, {
          style: getStyleFunction(dataType, colors),
          onEachFeature: function(feature, layer) {
            layer.on({
              click: function(e) {
                showProvinceInfo(feature.properties)
                e.originalEvent.propagatedFromFeature = true
              },
              mouseover: function(e) {
                e.target.setStyle({
                  weight: 3,
                  color: '#333'
                })
              },
              mouseout: function(e) {
                currentLayer.value.resetStyle(e.target)
              }
            })
          }
        }).addTo(map.value)

        // 添加省份名称标签
        addProvinceLabels(geojsonData)

        // 加载统计信息
        await loadYearStats(year)
        updateLegend(dataType, colors)

      } catch (error) {
        console.error('加载空间数据失败:', error)
        statsInfo.value = '数据加载失败'
      }
      loading.value = false

      // ✅ 修复 3: 增加安全检查后打印，解决 ReferenceError
      if (geojsonData && geojsonData.features) {
          console.log('接收到的GeoJSON要素数量:', geojsonData.features.length)
          console.log('所有省份:', geojsonData.features.map(f => f.properties.name))
      }
    }

    // 获取样式函数
    const getStyleFunction = (dataType, colors) => {
      return function(feature) {
        const props = feature.properties

        switch(dataType) {
          case 'gdp':
            const gdp = props.gdp || 0
            for (let i = 0; i < colors.gdp.breaks.length - 1; i++) {
              if (gdp >= colors.gdp.breaks[i] && gdp < colors.gdp.breaks[i + 1]) {
                return {
                  fillColor: colors.gdp.colors[i],
                  weight: 2,
                  opacity: 1,
                  color: '#333',
                  fillOpacity: 0.8
                }
              }
            }
            return {
              fillColor: colors.gdp.colors[colors.gdp.colors.length - 1],
              weight: 2,
              opacity: 1,
              color: '#333',
              fillOpacity: 0.8
            }

          case 'lisa':
            const lisaType = props.lisa_type
            return {
              fillColor: colors.lisa[lisaType] || '#cccccc',
              weight: 2,
              opacity: 1,
              color: '#333',
              fillOpacity: 0.8
            }

          case 'gi':
            const giType = props.gi_type
            return {
              fillColor: colors.gi[giType] || '#cccccc',
              weight: 2,
              opacity: 1,
              color: '#333',
              fillOpacity: 0.8
            }
        }
      }
    }

    // 更新图例
    const updateLegend = (dataType, colors) => {
      const legendContent = document.getElementById('legend-content')
      let legendHTML = ''

      if (dataType === 'gdp') {
        legendHTML += '<div style="font-weight: bold; margin-bottom: 8px; color: #333;">GDP(亿元)</div>'
        const scheme = colors.gdp || colorSchemes.default.gdp
        for (let i = 0; i < scheme.colors.length; i++) {
          legendHTML += `
            <div class="legend-item">
              <div class="legend-color" style="background-color: ${scheme.colors[i]}; border: 1px solid #666;"></div>
              <span style="color: #333;">${scheme.labels[i]}</span>
            </div>
          `
        }
      } else if (dataType === 'lisa') {
        legendHTML += '<div style="font-weight: bold; margin-bottom: 8px; color: #333;">LISA聚类</div>'
        const scheme = colors.lisa || colorSchemes.default.lisa
        for (const [type, color] of Object.entries(scheme)) {
          legendHTML += `
            <div class="legend-item">
              <div class="legend-color" style="background-color: ${color}; border: 1px solid #666;"></div>
              <span style="color: #333;">${type}</span>
            </div>
          `
        }
      } else if (dataType === 'gi') {
        legendHTML += '<div style="font-weight: bold; margin-bottom: 8px; color: #333;">Gi*热点</div>'
        const scheme = colors.gi || colorSchemes.default.gi
        for (const [type, color] of Object.entries(scheme)) {
          legendHTML += `
            <div class="legend-item">
              <div class="legend-color" style="background-color: ${color}; border: 1px solid #666;"></div>
              <span style="color: #333;">${type}</span>
            </div>
          `
        }
      }

      if (legendContent) {
        legendContent.innerHTML = legendHTML
      }
    }

    // 显示省份信息
    const showProvinceInfo = (props) => {
      provinceInfo.value = props
      showInfoPanel.value = true
    }

    // 加载年份统计信息
    const loadYearStats = async (year) => {
      try {
        const response = await getSpatialYearStats(year)
        const stats = response.data
        
        statsInfo.value = `
          ${year} 统计摘要
          省份数量: ${stats.province_count}
          GDP总量: ${formatNumber(stats.gdp_total)} 亿元
          平均GDP: ${formatNumber(stats.gdp_avg)} 亿元
          ${stats.moran_I ? `全局Moran's I: ${stats.moran_I.toFixed(3)}` : ''}
        `
      } catch (error) {
        console.error('加载统计信息失败:', error)
      }
    }

    // 刷新空间数据
    const refreshData = async () => {
      try {
        loading.value = true
        const response = await refreshSpatialData()
        const data = response.data

        if (data.status === 'success') {
          alert('空间分析数据刷新成功！')
          loadAvailableYears()
        } else {
          alert('刷新失败: ' + data.message)
        }
      } catch (error) {
        alert('刷新请求失败: ' + error.message)
      } finally {
        loading.value = false
      }
    }

    // 重置视图
    const resetView = () => {
      if (map.value) {
        map.value.setView([35, 105], 4)
        showInfoPanel.value = false
      }
    }

    // 格式化数字
    const formatNumber = (num) => {
      if (num === undefined || num === null) return 'N/A'
      return num.toLocaleString()
    }

    // 事件处理函数
    const handleYearChange = () => {
      if (currentYear.value) {
        loadSpatialData(currentYear.value, currentDataType.value)
      }
    }

    const handleDataTypeChange = () => {
      if (currentYear.value) {
        loadSpatialData(currentYear.value, currentDataType.value)
      }
    }

    const handleColorSchemeChange = () => {
      if (currentYear.value && currentDataType.value) {
        loadSpatialData(currentYear.value, currentDataType.value)
      }
    }

    // 生命周期
    onMounted(() => {
      initMap()
      loadAvailableYears()
    })

    onUnmounted(() => {
      if (map.value) {
        map.value.remove()
      }
    })

    return {
      mapContainer,
      currentYear,
      currentDataType,
      currentColorScheme,
      availableYears,
      statsInfo,
      showInfoPanel,
      provinceInfo,
      loading,
      refreshData,
      resetView,
      handleYearChange,
      handleDataTypeChange,
      handleColorSchemeChange,
      formatNumber
    }
  }
}
</script>

<style scoped>
.spatial-analysis-container {
  position: relative;
  width: 100%;
  height: 100vh;
  background-color: white; 
}

#map {
  height: 100%;
  width: 100%;
  background-color: white; 
}

.control-panel {
  position: absolute;
  top: 20px;
  right: 20px;
  background: white;
  padding: 20px;
  border-radius: 10px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  width: 300px;
  z-index: 1000;
}

.control-group {
  margin-bottom: 15px;
}

.control-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
  color: #333;
}

select, button {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 5px;
  font-size: 14px;
  background: white;
}

button {
  background: #1890ff;
  color: white;
  border: none;
  cursor: pointer;
  transition: background 0.3s;
}

button:hover {
  background: #40a9ff;
}

.legend {
  position: absolute;
  bottom: 20px;
  left: 20px;
  background: rgba(255, 255, 255, 0.95);
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  max-width: 250px;
  border: 1px solid #ddd;
  z-index: 1000;
}

.legend h4 {
  margin-bottom: 10px;
  color: #333;
  border-bottom: 1px solid #eee;
  padding-bottom: 5px;
  font-size: 14px;
}

.legend-item {
  display: flex;
  align-items: center;
  margin: 8px 0;
  font-size: 12px;
  min-height: 20px;
}

.legend-color {
  width: 20px;
  height: 20px;
  margin-right: 10px;
  border-radius: 3px;
  flex-shrink: 0;
}

/* 确保图例内容可见 */
:deep(#legend-content) {
  color: #333;
}

:deep(#legend-content .legend-item) {
  display: flex;
  align-items: center;
  margin: 8px 0;
}

:deep(#legend-content .legend-color) {
  width: 20px;
  height: 20px;
  margin-right: 10px;
  border-radius: 3px;
  display: block;
}
.info-panel {
  position: absolute;
  top: 20px;
  left: 20px;
  background: white;
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  max-width: 300px;
  z-index: 1000;
}

.info-panel h3 {
  color: #333;
  margin-bottom: 10px;
}

.stats {
  font-size: 12px;
  line-height: 1.5;
}

.loading {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: rgba(255,255,255,0.9);
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
  z-index: 2000;
}

/* 省份标签样式 */
:deep(.province-label-container) {
  background: none !important;
  border: none !important;
}

:deep(.province-label) {
  font-size: 12px;
  font-weight: 600;
  color: #333;
  text-shadow: 
    -1px -1px 0 #fff, 
    1px -1px 0 #fff, 
    -1px 1px 0 #fff, 
    1px 1px 0 #fff;
  pointer-events: none;
  text-align: center;
  white-space: nowrap;
  font-family: 'Microsoft YaHei', sans-serif;
}

/* 调整Leaflet地图样式 */
:deep(.leaflet-container) {
  background-color: white !important;
}

:deep(.leaflet-tile-container) {
  filter: none !important;
}
</style>