<template>
  <div class="province-comparison">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1><el-icon><DataAnalysis /></el-icon> 省份数据比较分析</h1>
      <div class="subtitle">选择多个省份和指标进行数据对比分析</div>
    </div>
    
    <!-- 选择区域 -->
    <div class="selection-section">
      <div class="section-title">
        <el-icon><Setting /></el-icon> 比较设置
      </div>
      
      <!-- 统一数据指标选择 -->
      <div class="data-selection">
        <div class="section-title">
          <el-icon><DataLine /></el-icon> 选择数据指标
        </div>
        <div class="data-control">
          <el-select 
            v-model="selectedData" 
            placeholder="请选择数据指标" 
            style="width: 100%; max-width: 400px;"
            class="text-center"
            size="large"
          >
            <el-option
              v-for="option in dataOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
              class="text-center"
            >
            </el-option>
          </el-select>
        </div>
      </div>
      
      <div class="comparison-controls">
        <!-- 动态添加的省份选择项 -->
        <div 
          v-for="(item, index) in comparisonItems" 
          :key="index" 
          class="comparison-item"
        >
          <h3 class="text-center">
            <el-icon><Location /></el-icon> 省份 {{ index + 1 }}
            <el-button 
              v-if="comparisonItems.length > 2"
              type="danger" 
              text 
              :icon="Close" 
              class="delete-btn"
              @click="removeProvince(index)"
            >
              删除
            </el-button>
          </h3>
          <div class="control-group">
            <label class="text-center">选择省份：</label>
            <el-select 
              v-model="item.province" 
              placeholder="请选择省份" 
              style="width: 100%"
              class="text-center"
            >
              <el-option
                v-for="option in provinceOptions"
                :key="option.value"
                :label="option.label"
                :value="option.value"
                class="text-center"
              >
              </el-option>
            </el-select>
          </div>
        </div>
        
        <!-- 添加省份按钮 -->
        <div class="add-province-container">
          <el-button 
            type="primary" 
            :icon="Plus" 
            @click="addProvince"
            class="add-btn"
            size="large"
          >
            添加省份
          </el-button>
        </div>
      </div>
      
      <!-- 操作按钮 -->
      <div class="actions">
        <el-button type="primary" :icon="Refresh" @click="resetSelection" size="large" class="action-btn">重置选择</el-button>
        <el-button type="success" :icon="DataLine" @click="showChartDialog" size="large" class="action-btn" :loading="loading">查看图表</el-button>
      </div>
    </div>

    <!-- 图表展示弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="85%"
      top="5vh"
      class="chart-dialog"
      :close-on-click-modal="false"
      @closed="handleDialogClosed"
      :show-close="true"
      :show-header="false"
    >
      <!-- 图表容器 -->
      <div class="chart-container" v-loading="loading">
        <div id="chartContainer" ref="chartContainer" style="width: 100%; height: 65vh;"></div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, nextTick } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import {
  DataAnalysis,
  Setting,
  Location,
  Refresh,
  DataLine,
  Plus,
  Close
} from '@element-plus/icons-vue'
import {
  getPopulationData,
  getFinancialExpenditureData,
  getQuarterlyData,
  getQuarterlyIndexData,
  getAnnualData,
  getConsumerGoodsData
} from '../api/index'

// 响应式数据
const dialogVisible = ref(false)
const selectedData = ref('')
const loading = ref(false)
const chartContainer = ref<HTMLElement | null>(null)
let chartInstance: echarts.ECharts | null = null

// 省份选项
const provinceOptions = ref([
  { value: 'beijing', label: '北京市' },
  { value: 'tianjin', label: '天津市' },
  { value: 'hebei', label: '河北省' },
  { value: 'shanxi', label: '山西省' },
  { value: 'neimenggu', label: '内蒙古自治区' },
  { value: 'liaoning', label: '辽宁省' },
  { value: 'jilin', label: '吉林省' },
  { value: 'heilongjiang', label: '黑龙江省' },
  { value: 'shanghai', label: '上海市' },
  { value: 'jiangsu', label: '江苏省' },
  { value: 'zhejiang', label: '浙江省' },
  { value: 'anhui', label: '安徽省' },
  { value: 'fujian', label: '福建省' },
  { value: 'jiangxi', label: '江西省' },
  { value: 'shandong', label: '山东省' },
  { value: 'henan', label: '河南省' },
  { value: 'hubei', label: '湖北省' },
  { value: 'hunan', label: '湖南省' },
  { value: 'guangdong', label: '广东省' },
  { value: 'guangxi', label: '广西壮族自治区' },
  { value: 'hainan', label: '海南省' },
  { value: 'chongqing', label: '重庆市' },
  { value: 'sichuan', label: '四川省' },
  { value: 'guizhou', label: '贵州省' },
  { value: 'yunnan', label: '云南省' },
  { value: 'xizang', label: '西藏自治区' },
  { value: 'shaanxi', label: '陕西省' },
  { value: 'gansu', label: '甘肃省' },
  { value: 'qinghai', label: '青海省' },
  { value: 'ningxia', label: '宁夏回族自治区' },
  { value: 'xinjiang', label: '新疆维吾尔自治区' },
  { value: 'taiwan', label: '台湾省' },
  { value: 'xianggang', label: '香港特别行政区' },
  { value: 'aomen', label: '澳门特别行政区' }
])

// 数据选项
const dataOptions = ref([
  { value: 'population', label: '人口数据（万人）' },
  { value: 'financialExpenditure', label: '地方财政支出数据（亿元）' },
  { value: 'quarterly', label: '季度数据（亿元）' },
  { value: 'quarterlyIndex', label: '季度指数数据' },
  { value: 'annual', label: '年度数据（亿元）' },
  { value: 'consumerGoods', label: '消费品数据（亿元）' }
])

// 省份比较项数组
const comparisonItems = ref([
  { province: '' },
  { province: '' }
])

// 表格数据
const tableData = ref<any[]>([])

// 计算属性
const selectedProvinces = computed(() => {
  return comparisonItems.value
    .map(item => {
      const province = provinceOptions.value.find(p => p.value === item.province)
      return province ? { value: item.province, label: province.label } : null
    })
    .filter(Boolean) as { value: string; label: string }[]
})

const dialogTitle = computed(() => {
  const dataType = dataOptions.value.find(d => d.value === selectedData.value)?.label || '数据'
  const provinces = selectedProvinces.value.map(p => p.label).join(' vs ')
  return `${provinces} ${dataType}对比`
})

// 添加省份
const addProvince = () => {
  if (comparisonItems.value.length < 6) {
    comparisonItems.value.push({ province: '' })
  } else {
    ElMessage.warning('最多只能比较6个省份')
  }
}

// 删除省份
const removeProvince = (index: number) => {
  if (comparisonItems.value.length > 2) {
    comparisonItems.value.splice(index, 1)
  }
}

// 重置选择
const resetSelection = () => {
  comparisonItems.value = [
    { province: '' },
    { province: '' }
  ]
  selectedData.value = ''
  tableData.value = []
}

// 格式化数字显示
const formatNumber = (num: number) => {
  if (num === null || num === undefined) return '-'
  return num.toLocaleString('zh-CN')
}



const initChart = (apiResponseData: any, selectedProvinces: {value: string, label: string}[]) => {
  if (!chartContainer.value) return;
  
  // 销毁现有图表实例
  if (chartInstance) {
    chartInstance.dispose();
  }
  
  // 创建新的图表实例
  chartInstance = echarts.init(chartContainer.value);
  
  // 确保数据是数组格式
  const apiDataArray = Array.isArray(apiResponseData) ? apiResponseData : [apiResponseData];
  
  // 判断是否为季度数据
  const isQuarterlyData = selectedData.value === 'quarterly' || selectedData.value === 'quarterlyIndex';
  
  let xAxisData: string[] = [];
  let seriesData: any[] = [];
  
  if (isQuarterlyData) {
    // 处理季度数据格式
    
    // 从API数据中提取所有季度并排序
    const allQuarters = new Set<string>();
    selectedProvinces.forEach(province => {
      const provinceData = apiDataArray.find((item: any) => {
        return item.地区 === province.label || 
               item.province === province.label ||
               item.name === province.label ||
               item.省份 === province.label;
      });
      if (provinceData) {
        Object.keys(provinceData).forEach(key => {
          if (key.includes('年') && key.includes('季度') && key !== '_pk' && key !== '地区') {
            allQuarters.add(key);
          }
        });
      }
    });
    
    // 对季度进行排序：按年份和季度排序
    xAxisData = Array.from(allQuarters).sort((a, b) => {
      // 提取年份和季度数字
      const yearA = parseInt(a.split('年')[0]);
      const quarterA = parseInt(a.split('第')[1].split('季度')[0]);
      const yearB = parseInt(b.split('年')[0]);
      const quarterB = parseInt(b.split('第')[1].split('季度')[0]);
      
      if (yearA !== yearB) return yearA - yearB;
      return quarterA - quarterB;
    });
    
    // 构建系列数据
    seriesData = selectedProvinces.map((province, index) => {
      const provinceData = apiDataArray.find((item: any) => {
        return item.地区 === province.label || 
               item.province === province.label ||
               item.name === province.label ||
               item.省份 === province.label;
      });
      
      const dataValues = xAxisData.map(quarter => {
        // 直接从季度数据对象中获取值
        const value = provinceData ? provinceData[quarter] : null;
        return value ? parseFloat(value) : null;
      });
      
      // 生成不同的颜色
      const colors = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272'];
      
      return {
        name: province.label,
        type: 'line',
        data: dataValues,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: {
          width: 3
        },
        itemStyle: {
          color: colors[index % colors.length]
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: colors[index % colors.length] + '80' },
            { offset: 1, color: colors[index % colors.length] + '10' }
          ])
        }
      };
    });
  } else {
    // 处理年度数据
    
    const allYears = new Set<string>();
    selectedProvinces.forEach(province => {
      const provinceData = apiDataArray.find((item: any) => {
        return item.地区 === province.label || 
               item.province === province.label ||
               item.name === province.label ||
               item.省份 === province.label;
      });
      if (provinceData) {
        Object.keys(provinceData).forEach(key => {
          if (key.includes('年') && !key.includes('季度') && key !== '_pk' && key !== '地区') {
            allYears.add(key);
          }
        });
      }
    });
    
    // 对年份进行排序
    xAxisData = Array.from(allYears).sort((a, b) => parseInt(a) - parseInt(b));
    
    // 构建系列数据
    seriesData = selectedProvinces.map((province, index) => {
      const provinceData = apiDataArray.find((item: any) => {
        return item.地区 === province.label || 
               item.province === province.label ||
               item.name === province.label ||
               item.省份 === province.label;
      });
      
      const dataValues = xAxisData.map(year => {
        const value = provinceData ? provinceData[year] : null;
        return value ? parseFloat(value) : null;
      });
      
      // 生成不同的颜色
      const colors = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272'];
      
      return {
        name: province.label,
        type: 'line',
        data: dataValues,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: {
          width: 3
        },
        itemStyle: {
          color: colors[index % colors.length]
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: colors[index % colors.length] + '80' },
            { offset: 1, color: colors[index % colors.length] + '10' }
          ])
        }
      };
    });
  }
  
  // 图表配置选项 - 修改了标题和图例的间距
  const option = {
    title: {
      text: dialogTitle.value,
      left: 'center',
      top: '10px', // 标题距离顶部
      textStyle: {
        fontSize: 18,
        fontWeight: 'bold'
      },
      padding: [10, 0, 30, 0] // 增加底部padding，拉开与图例的距离
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
        label: {
          backgroundColor: '#6a7985'
        }
      },
      formatter: function (params: any) {
        let result = `${params[0].axisValue}<br/>`;
        params.forEach((param: any) => {
          const value = param.value !== null ? param.value.toLocaleString('zh-CN') : '无数据';
          result += `${param.marker} ${param.seriesName}: ${value}<br/>`;
        });
        return result;
      }
    },
    legend: {
      data: selectedProvinces.map(p => p.label),
      top: '60px', // 图例距离顶部，与标题拉开距离
      type: 'scroll',
      itemGap: 15 // 图例项之间的间距
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '100px', // 调整grid顶部位置
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: xAxisData,
      axisLabel: {
        rotate: 45
      }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: function (value: number) {
          return value.toLocaleString('zh-CN');
        }
      }
    },
    series: seriesData
  };
  
  // 设置图表选项
  chartInstance.setOption(option);
  
  // 响应窗口大小变化
  window.addEventListener('resize', function() {
    chartInstance?.resize();
  });
}

// 处理弹窗关闭
const handleDialogClosed = () => {
  if (chartInstance) {
    chartInstance.dispose();
    chartInstance = null;
  }
}

const showChartDialog = async () => {
  // 检查是否所有项都已选择
  const hasEmptyProvince = comparisonItems.value.some(item => !item.province)
  
  if (hasEmptyProvince || !selectedData.value) {
    ElMessage.warning('请完整选择所有省份和数据指标')
    return
  }
  
  loading.value = true;
  
  try {
    // 获取选中的省份代码和对应的中文名称
    const selectedProvinces = comparisonItems.value.map(item => ({
      value: item.province,
      label: provinceOptions.value.find(p => p.value === item.province)?.label || ''
    })).filter(p => p.value);
    
    // 根据选择的数据指标调用对应的API
    let apiResponse;
    switch(selectedData.value) {
      case 'population':
        apiResponse = await getPopulationData();
        break;
      case 'financialExpenditure':
        apiResponse = await getFinancialExpenditureData();
        break;
      case 'quarterly':
        apiResponse = await getQuarterlyData();
        break;
      case 'quarterlyIndex':
        apiResponse = await getQuarterlyIndexData();
        break;
      case 'annual':
        apiResponse = await getAnnualData();
        break;
      case 'consumerGoods':
        apiResponse = await getConsumerGoodsData();
        break;
      default:
        throw new Error('未知的数据指标');
    }
    
    // 调试：打印API返回的数据结构
    console.log('API返回数据:', apiResponse);
    
    // 处理API返回的数据结构
    let apiResponseData = apiResponse.data;
    
    // 处理数据结构问题：确保是数组格式
    if (apiResponseData && typeof apiResponseData === 'object' && !Array.isArray(apiResponseData)) {
      // 如果是对象，检查是否有data属性
      if (apiResponseData.data && Array.isArray(apiResponseData.data)) {
        apiResponseData = apiResponseData.data;
      } else {
        // 如果是单个对象，包装成数组
        apiResponseData = [apiResponseData];
      }
    }
    
    // 判断是否为季度数据
    const isQuarterlyData = selectedData.value === 'quarterly' || selectedData.value === 'quarterlyIndex';
    
    // 处理表格数据
    let tableDataTemp: any[] = [];
    
    if (isQuarterlyData) {
      // 处理季度数据表格
      const allQuarters = new Set<string>();
      
      // 确保apiResponseData是数组
      const apiDataArray = Array.isArray(apiResponseData) ? apiResponseData : [apiResponseData];
      
      selectedProvinces.forEach(province => {
        // 从API数据中查找对应省份的数据（增强匹配逻辑）
        const provinceData = apiDataArray.find((item: any) => {
          // 多种可能的字段名匹配
          return item.地区 === province.label || 
                 item.province === province.label ||
                 item.name === province.label ||
                 item.省份 === province.label;
        });
        
        if (provinceData) {
          Object.keys(provinceData).forEach(key => {
            if (key.includes('年') && key.includes('季度') && key !== '_pk' && key !== '地区') {
              allQuarters.add(key);
            }
          });
        }
      });
      
      // 对季度进行排序
      const sortedQuarters = Array.from(allQuarters).sort((a, b) => {
        const yearA = parseInt(a.split('年')[0]);
        const quarterA = parseInt(a.split('第')[1].split('季度')[0]);
        const yearB = parseInt(b.split('年')[0]);
        const quarterB = parseInt(b.split('第')[1].split('季度')[0]);
        
        if (yearA !== yearB) return yearA - yearB;
        return quarterA - quarterB;
      });
      
      tableDataTemp = sortedQuarters.map(quarter => {
        const row: any = { year: quarter };
        selectedProvinces.forEach(province => {
          const provinceData = apiDataArray.find((item: any) => {
            return item.地区 === province.label || 
                   item.province === province.label ||
                   item.name === province.label ||
                   item.省份 === province.label;
          });
          row[province.value] = provinceData ? provinceData[quarter] : null;
        });
        return row;
      });
    } else {
      // 处理年度数据表格
      const allYears = new Set<string>();
      
      // 确保apiResponseData是数组
      const apiDataArray = Array.isArray(apiResponseData) ? apiResponseData : [apiResponseData];
      
      selectedProvinces.forEach(province => {
        const provinceData = apiDataArray.find((item: any) => {
          return item.地区 === province.label || 
                 item.province === province.label ||
                 item.name === province.label ||
                 item.省份 === province.label;
        });
        
        if (provinceData) {
          Object.keys(provinceData).forEach(key => {
            if (key.includes('年') && !key.includes('季度') && key !== '_pk' && key !== '地区') {
              allYears.add(key);
            }
          });
        }
      });
      
      // 对年份进行排序
      const sortedYears = Array.from(allYears).sort((a, b) => parseInt(a) - parseInt(b));
      
      tableDataTemp = sortedYears.map(year => {
        const row: any = { year };
        selectedProvinces.forEach(province => {
          const provinceData = apiDataArray.find((item: any) => {
            return item.地区 === province.label || 
                   item.province === province.label ||
                   item.name === province.label ||
                   item.省份 === province.label;
          });
          row[province.value] = provinceData ? provinceData[year] : null;
        });
        return row;
      });
    }
    
    tableData.value = tableDataTemp;
    
    // 显示弹窗
    dialogVisible.value = true;
    
    // 使用nextTick确保DOM已更新
    nextTick(() => {
      initChart(apiResponseData, selectedProvinces);
    });
    
  } catch (error) {
    console.error('获取数据失败:', error);
    ElMessage.error('数据获取失败，请重试');
  } finally {
    loading.value = false;
  }
}
// 组件卸载时清理
onMounted(() => {
  return () => {
    if (chartInstance) {
      chartInstance.dispose();
    }
  }
})
</script>

<style scoped>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  font-family: "Helvetica Neue", Helvetica, "PingFang SC", "Hiragino Sans GB", Arial, sans-serif;
}

body {
  background-color: #f5f7fa;
  color: #333;
  padding: 20px;
  min-height: 100vh;
}

.province-comparison {
  max-width: 1200px;
  margin: 0 auto;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  overflow: hidden;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.page-header {
  padding: 20px 24px;
  border-bottom: 1px solid #e4e7ed;
  background: linear-gradient(135deg, #409EFF 0%, #66b1ff 100%);
  color: white;
  flex-shrink: 0;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
}

.page-header h1 i {
  margin-right: 10px;
  font-size: 28px;
}

.page-header .subtitle {
  margin-top: 8px;
  font-size: 14px;
  opacity: 0.9;
  text-align: center;
}

.selection-section {
  padding: 24px;
  border-bottom: 1px solid #e4e7ed;
  flex-shrink: 0;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
  color: #409EFF;
  display: flex;
  align-items: center;
  justify-content: center;
}

.section-title i {
  margin-right: 8px;
}

.data-selection {
  margin-bottom: 24px;
  text-align: center;
}

.data-control {
  display: flex;
  justify-content: center;
}

.comparison-controls {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
  justify-content: center;
}

.comparison-item {
  flex: 0 0 calc(33.333% - 20px);
  min-width: 300px;
  padding: 16px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  background: #f9fafc;
  display: flex;
  flex-direction: column;
}

.comparison-item h3 {
  font-size: 15px;
  margin-bottom: 12px;
  color: #606266;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.comparison-item h3 i {
  margin-right: 6px;
  color: #409EFF;
}

.delete-btn {
  padding: 4px 8px;
  font-size: 12px;
}

.control-group {
  margin-bottom: 16px;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.control-group:last-child {
  margin-bottom: 0;
}

.control-group label {
  display: block;
  margin-bottom: 6px;
  font-size: 14px;
  color: #606266;
}

.text-center {
  text-align: center;
}

.add-province-container {
  display: flex;
  justify-content: center;
  width: 100%;
  margin-top: 10px;
}

.add-btn {
  width: 200px;
  font-size: 16px;
  padding: 12px 20px;
  height: auto;
}

.actions {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 30px;
}

.action-btn {
  font-size: 16px;
  padding: 12px 30px;
  height: auto;
  min-width: 140px;
}

/* 图表弹窗样式 */
.chart-container {
  margin-bottom: 20px;
}

.data-table-container {
  margin-top: 30px;
}

.data-table-container h3 {
  margin-bottom: 15px;
  color: #409EFF;
  text-align: center;
}

:deep(.chart-dialog .el-dialog__body) {
  padding: 15px 20px; /* 减少内边距 */
}

:deep(.chart-dialog .el-dialog) {
  border-radius: 8px;
  overflow: hidden;
  max-height: 90vh; /* 限制最大高度 */
}

:deep(.chart-dialog .el-dialog__header) {
  background: linear-gradient(135deg, #409EFF 0%, #66b1ff 100%);
  margin: 0;
  padding: 12px 20px; /* 减少头部内边距 */
}

:deep(.chart-dialog .el-dialog__title) {
  color: white;
  font-weight: 600;
  font-size: 16px; /* 稍微减小标题字体 */
}

:deep(.chart-dialog .el-dialog__headerbtn) {
  top: 12px; /* 调整关闭按钮位置 */
}

:deep(.chart-dialog .el-dialog__headerbtn .el-dialog__close) {
  color: white;
  font-size: 18px; /* 调整关闭图标大小 */
}

:deep(.el-table) {
  font-size: 14px;
}

:deep(.el-table th) {
  background-color: #f5f7fa;
  font-weight: 600;
}

:deep(.el-select .el-input__inner) {
  text-align: center;
}

:deep(.el-select .el-input__suffix) {
  right: 10px;
}

:deep(.el-option) {
  text-align: center;
}

:deep(.el-button--large) {
  font-size: 16px;
  padding: 12px 24px;
}

/* 隐藏底部footer */
:deep(.chart-dialog .el-dialog__footer) {
  display: none;
}

@media (max-width: 768px) {
  .comparison-controls {
    flex-direction: column;
    align-items: center;
  }
  
  .comparison-item {
    flex: 0 0 100%;
    min-width: 100%;
  }
  
  .actions {
    flex-direction: column;
    align-items: center;
  }
  
  .action-btn {
    width: 100%;
    max-width: 300px;
  }
  
  .data-control {
    justify-content: stretch;
  }
  
  .data-control .el-select {
    max-width: 100% !important;
  }
  
  :deep(.chart-dialog) {
    width: 95% !important; /* 移动端保持较大宽度 */
    top: 3vh !important;
  }
  
  :deep(#chartContainer) {
    height: 50vh !important; /* 移动端调整高度 */
  }
}
</style>