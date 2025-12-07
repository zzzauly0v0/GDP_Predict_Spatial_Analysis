<template>
  <div class="gdp-prediction-container">
    <!-- 标题区域 -->
    <div class="header-section">
      <h2>GDP预测分析</h2>
    </div>

    <!-- 数据来源选择区域 -->
    <div class="control-section">
      <el-card shadow="hover">
        <template #header>
          <div class="card-header">
            <span>数据来源选择</span>
          </div>
        </template>
        
        <div class="control-content">
          <el-radio-group v-model="dataSource" @change="handleDataSourceChange">
            <el-radio label="province">使用省份数据</el-radio>
            <el-radio label="custom">导入自定义数据</el-radio>
          </el-radio-group>
        </div>
      </el-card>
    </div>

    <!-- 省份选择区域 -->
    <div class="control-section" v-if="dataSource === 'province'">
      <el-card shadow="hover">
        <template #header>
          <div class="card-header">
            <span>预测参数设置</span>
          </div>
        </template>
        
        <div class="control-content">
          <el-row :gutter="20" align="middle">
            <el-col :span="8">
              <el-form label-width="100px">
                <el-form-item label="选择省份">
                  <el-select 
                    v-model="selectedProvince" 
                    placeholder="请选择省份"
                    style="width: 100%"
                    @change="handleProvinceChange"
                  >
                    <el-option
                      v-for="province in provinces"
                      :key="province"
                      :label="province"
                      :value="province"
                    />
                  </el-select>
                </el-form-item>
              </el-form>
            </el-col>
            
            <el-col :span="16">
              <div class="action-buttons">
                <el-button 
                  type="primary" 
                  @click="loadData"
                  :loading="loading"
                >
                  加载数据
                </el-button>
                <el-button 
                  type="success" 
                  @click="runPrediction"
                  :disabled="!selectedProvince"
                  :loading="predicting"
                >
                  执行预测
                </el-button>
              </div>
            </el-col>
          </el-row>
        </div>
      </el-card>
    </div>

    <!-- 自定义数据上传区域 -->
    <div class="control-section" v-if="dataSource === 'custom'">
      <el-card shadow="hover">
        <template #header>
          <div class="card-header">
            <span>自定义数据上传</span>
          </div>
        </template>
        
        <div class="control-content">
          <!-- 省份选择 -->
          <el-row :gutter="20" align="middle" class="mb-20">
            <el-col :span="24">
              <el-form label-width="100px">
                <el-form-item label="选择模型省份">
                  <el-select 
                    v-model="selectedProvinceForCustom" 
                    placeholder="请选择省份以使用对应预测模型"
                    style="width: 100%"
                  >
                    <el-option
                      v-for="province in provinces"
                      :key="province"
                      :label="province"
                      :value="province"
                    />
                  </el-select>
                  <div class="el-upload__tip">
                    请选择您要使用的预测模型对应的省份
                  </div>
                </el-form-item>
              </el-form>
            </el-col>
          </el-row>
          
          <el-row :gutter="20">
            <el-col :span="12">
              <el-upload
                class="upload-demo"
                action=""
                :auto-upload="false"
                :on-change="handleFileUpload"
                :show-file-list="false"
                accept=".csv,.xlsx,.xls"
              >
                <el-button type="primary" :disabled="!selectedProvinceForCustom">
                  选择数据文件
                </el-button>
                <template #tip>
                  <div class="el-upload__tip">
                    支持CSV，包含年份和GDP两列
                  </div>
                </template>
              </el-upload>
            </el-col>
            
            <el-col :span="12">
              <div class="action-buttons">
                <el-button 
                  type="success" 
                  @click="runCustomPrediction"
                  :disabled="!customData.length || !selectedProvinceForCustom"
                  :loading="predicting"
                >
                  执行预测
                </el-button>
              </div>
            </el-col>
          </el-row>
          
          <div v-if="customData.length" class="custom-data-preview">
            <h4>数据预览 (前5行)</h4>
            <el-table 
              :data="customData.slice(0, 5)"
              height="200"
              stripe
              border
            >
              <el-table-column prop="year" label="年份" width="100" />
              <el-table-column prop="gdp" label="GDP（亿元）">
                <template #default="{ row }">
                  {{ formatNumber(row.gdp) }}
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 图表展示区域 -->
    <div class="chart-section" v-if="hasData">
      <el-card shadow="hover">
        <template #header>
          <div class="card-header">
            <span>GDP趋势图表</span>
            <el-button 
              type="text" 
              @click="toggleChartType"
              size="small"
            >
              切换为{{ chartType === 'line' ? '柱状图' : '折线图' }}
            </el-button>
          </div>
        </template>
        
        <div id="gdp-chart" style="height: 400px;"></div>
      </el-card>
    </div>

    <!-- 数据展示区域 -->
    <div class="data-section">
      <el-row :gutter="20">
        <!-- 历史数据 -->
        <el-col :span="12">
          <el-card shadow="hover" class="data-card">
            <template #header>
              <div class="card-header">
                <span>历史GDP数据</span>
                <el-tag v-if="historicalData.length" type="success">
                  共 {{ historicalData.length }} 条记录
                </el-tag>
              </div>
            </template>
            
            <div v-loading="loading">
              <el-table 
                v-if="historicalData.length"
                :data="historicalData"
                height="300"
                stripe
              >
                <el-table-column prop="year" label="年份" width="100" sortable />
                <el-table-column prop="gdp" label="GDP（亿元）">
                  <template #default="{ row }">
                    {{ formatNumber(row.gdp) }}
                  </template>
                </el-table-column>
              </el-table>
              
              <el-empty v-else description="暂无数据" />
            </div>
          </el-card>
        </el-col>

        <!-- 预测结果 -->
        <el-col :span="12">
          <el-card shadow="hover" class="data-card">
            <template #header>
              <div class="card-header">
                <span>GDP预测结果</span>
                <el-tag v-if="predictionData.length" type="warning">
                  未来 {{ predictionData.length }} 年预测
                </el-tag>
                <el-tag v-if="dataSource === 'custom' && selectedProvinceForCustom" type="info">
                  使用 {{ selectedProvinceForCustom }} 模型
                </el-tag>
              </div>
            </template>
            
            <div v-loading="predicting">
              <el-table 
                v-if="predictionData.length"
                :data="predictionData"
                height="300"
                stripe
              >
                <el-table-column prop="year" label="年份" width="100" />
                <el-table-column prop="gdp" label="预测GDP（亿元）">
                  <template #default="{ row }">
                    <span class="prediction-value">{{ formatNumber(row.gdp) }}</span>
                  </template>
                </el-table-column>
              </el-table>
              
              <el-empty v-else description="请先执行预测" />
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 统计信息 -->
    <div class="stats-section" v-if="hasData">
      <el-card shadow="hover">
        <template #header>
          <span>统计信息</span>
        </template>
        <el-row :gutter="20">
          <el-col :span="6" v-for="stat in statistics" :key="stat.title">
            <div class="stat-item">
              <div class="stat-title">{{ stat.title }}</div>
              <div class="stat-value" :style="stat.style">
                {{ stat.value }}{{ stat.suffix }}
              </div>
            </div>
          </el-col>
        </el-row>
      </el-card>
    </div>

    <!-- 训练指标展示区域 -->
    <div v-if="showMetrics && metricsData" class="metrics-section">
      <el-card shadow="hover">
        <template #header>
          <div class="card-header">
            <span>📊 模型训练指标</span>
            <el-tag type="info" size="small">{{ metricsData.province }}</el-tag>
          </div>
        </template>
        
        <el-row :gutter="20" class="mb-3">
          <el-col :span="12">
            <h6>📋 训练信息</h6>
            <div class="info-box">
              <p><strong>省份:</strong> {{ metricsData.province }}</p>
              <p><strong>训练时间:</strong> {{ new Date(metricsData.saved_at).toLocaleString() }}</p>
              <p><strong>训练轮次:</strong> {{ metricsData.num_epochs }}</p>
            </div>
          </el-col>
          <el-col :span="12">
            <h6>⚙️ 超参数</h6>
            <div class="info-box" v-if="metricsData.hyperparams">
              <p><strong>输入特征数:</strong> {{ metricsData.hyperparams.input_feature_size }}</p>
              <p><strong>隐藏层大小:</strong> {{ metricsData.hyperparams.hidden_size }}</p>
              <p><strong>LSTM层数:</strong> {{ metricsData.hyperparams.num_layers }}</p>
              <p><strong>预测步数:</strong> {{ metricsData.hyperparams.predict_steps }}</p>
              <p><strong>窗口大小:</strong> {{ metricsData.hyperparams.window_size }}</p>
              <p><strong>批次大小:</strong> {{ metricsData.hyperparams.batch_size }}</p>
            </div>
          </el-col>
        </el-row>
        
        <el-row>
          <el-col :span="24">
            <h6>📈 训练过程指标</h6>
            <div class="data-table-container" style="max-height: 400px;">
              <el-table 
                :data="formatMetricsForTable" 
                stripe 
                border
                size="small"
                :row-class-name="({ row }) => row.isLast5 ? 'success-row' : ''"
              >
                <el-table-column prop="epoch" label="轮次" width="80" />
                <el-table-column prop="train_loss" label="训练损失" width="100">
                  <template #default="{ row }">
                    {{ row.train_loss.toFixed(4) }}
                  </template>
                </el-table-column>
                <el-table-column prop="train_mae" label="训练MAE" width="100">
                  <template #default="{ row }">
                    {{ row.train_mae.toFixed(4) }}
                  </template>
                </el-table-column>
                <el-table-column prop="train_mse" label="训练MSE" width="100">
                  <template #default="{ row }">
                    {{ row.train_mse.toFixed(4) }}
                  </template>
                </el-table-column>
                <el-table-column prop="train_mape" label="训练MAPE" width="110">
                  <template #default="{ row }">
                    {{ row.train_mape.toFixed(4) }}
                  </template>
                </el-table-column>
                <el-table-column prop="test_loss" label="测试损失" width="100">
                  <template #default="{ row }">
                    {{ row.test_loss.toFixed(4) }}
                  </template>
                </el-table-column>
                <el-table-column prop="test_mae" label="测试MAE" width="100">
                  <template #default="{ row }">
                    {{ row.test_mae.toFixed(4) }}
                  </template>
                </el-table-column>
                <el-table-column prop="test_mse" label="测试MSE" width="100">
                  <template #default="{ row }">
                    {{ row.test_mse.toFixed(4) }}
                  </template>
                </el-table-column>
                <el-table-column prop="test_mape" label="测试MAPE" width="110">
                  <template #default="{ row }">
                    {{ row.test_mape.toFixed(4) }}
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </el-col>
        </el-row>
      </el-card>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { getGDPHistoricalData, getGDPPrediction, getGDPMetrics, getPopulationData } from '../api/index'

export default {
  name: 'GDPPrediction',
  
  setup() {
    // 响应式数据
    const selectedProvince = ref('')
    const selectedProvinceForCustom = ref('') // 专门用于自定义数据的省份选择
    const dataSource = ref('province') // 'province' 或 'custom'
    const loading = ref(false)
    const predicting = ref(false)
    const historicalData = ref([])
    const predictionData = ref([])
    const customData = ref([])
    const chartType = ref('line') // 'line' 或 'bar'
    const provinces = ref([]) // 改为响应式数组
    const metricsData = ref(null) // 训练指标数据
    const showMetrics = ref(false) // 控制指标显示
    let chart = null

    // 计算属性
    const hasData = computed(() => {
      return historicalData.value.length > 0 || predictionData.value.length > 0
    })

    const statistics = computed(() => {
      const stats = []
      
      if (historicalData.value.length > 0) {
        const latestHistorical = historicalData.value[historicalData.value.length - 1]
        stats.push({
          title: '最新历史GDP',
          value: formatNumber(latestHistorical.gdp),
          suffix: '亿元',
          style: { color: '#409EFF' }
        })
      }
      
      if (predictionData.value.length > 0) {
        const firstPrediction = predictionData.value[0]
        const lastPrediction = predictionData.value[predictionData.value.length - 1]
        
        stats.push({
          title: '预测起始值',
          value: formatNumber(firstPrediction.gdp),
          suffix: '亿元',
          style: { color: '#E6A23C' }
        })
        
        stats.push({
          title: '预测最终值',
          value: formatNumber(lastPrediction.gdp),
          suffix: '亿元',
          style: { color: '#67C23A' }
        })
        
        const growthRate = ((lastPrediction.gdp - firstPrediction.gdp) / firstPrediction.gdp * 100).toFixed(2)
        stats.push({
          title: '预测期间增长率',
          value: growthRate,
          suffix: '%',
          style: { color: growthRate >= 0 ? '#F56C6C' : '#909399' }
        })
      }
      
      return stats
    })

    // 格式化训练指标数据用于表格显示
    const formatMetricsForTable = computed(() => {
      if (!metricsData.value || !metricsData.value.metrics) return [];
      
      const metrics = metricsData.value.metrics;
      const numEpochs = metrics.train_loss.length;
      const result = [];
      
      for (let i = 0; i < numEpochs; i++) {
        result.push({
          epoch: i + 1,
          train_loss: metrics.train_loss[i],
          train_mae: metrics.train_mae[i],
          train_mse: metrics.train_mse[i],
          train_mape: metrics.train_mape[i],
          test_loss: metrics.test_loss[i],
          test_mae: metrics.test_mae[i],
          test_mse: metrics.test_mse[i],
          test_mape: metrics.test_mape[i],
          isLast5: i >= numEpochs - 5
        });
      }
      
      return result;
    });

    // 方法
    const handleDataSourceChange = () => {
      historicalData.value = []
      predictionData.value = []
      customData.value = []
      if (chart) {
        chart.dispose()
        chart = null
      }
    }

    const handleProvinceChange = () => {
      historicalData.value = []
      predictionData.value = []
      if (chart) {
        chart.dispose()
        chart = null
      }
    }

    const loadProvinces = () => {
      // 使用固定的省份列表（与后端 PROVINCES 一致）
      provinces.value = [
        "北京市", "天津市", "上海市", "重庆市", 
        "内蒙古自治区", "广西壮族自治区", "西藏自治区", 
        "宁夏回族自治区", "新疆维吾尔自治区",
        "河北省", "山西省", "辽宁省", "吉林省", "黑龙江省",
        "江苏省", "浙江省", "安徽省", "福建省", "江西省",
        "山东省", "河南省", "湖北省", "湖南省", "广东省",
        "海南省", "四川省", "贵州省", "云南省", "陕西省",
        "甘肃省", "青海省"
      ];
      console.log('已加载省份列表，共', provinces.value.length, '个省份');
    }

    const loadData = async () => {
      if (!selectedProvince.value) {
        ElMessage.warning('请先选择省份')
        return
      }

      loading.value = true
      try {
        const response = await getGDPHistoricalData(selectedProvince.value)
        console.log('历史数据响应:', response)
        
        // 适配不同的API响应格式
        // axios 返回的数据在 response.data 中
        const data = response.data;
        
        if (data.success && data.data) {
          historicalData.value = data.data
          ElMessage.success('历史数据加载成功')
          
          // 加载后更新图表
          nextTick(() => {
            renderChart()
          })
        } else {
          ElMessage.error('数据加载失败：' + (data.message || '未知错误'))
        }
      } catch (error) {
        console.error('加载历史数据错误:', error)
        ElMessage.error('数据加载异常：' + error.message)
      } finally {
        loading.value = false
      }
    }

    const runPrediction = async () => {
      if (!selectedProvince.value) {
        ElMessage.warning('请先选择省份')
        return
      }

      predicting.value = true
      try {
        // 并行获取历史数据、预测数据和训练指标
        const [historicalRes, predictionRes, metricsRes] = await Promise.all([
          getGDPHistoricalData(selectedProvince.value),
          getGDPPrediction(selectedProvince.value),
          getGDPMetrics(selectedProvince.value)
        ]);

        console.log('历史数据:', historicalRes);
        console.log('预测数据:', predictionRes);
        console.log('训练指标:', metricsRes);

        // axios 返回的数据在 response.data 中
        const histData = historicalRes.data;
        const predData = predictionRes.data;
        const metricsDataRes = metricsRes.data;

        // 检查响应
        if (!histData.success) {
          throw new Error(`获取历史数据失败: ${histData.message}`);
        }
        if (!predData.success) {
          throw new Error(`获取预测数据失败: ${predData.message}`);
        }
        
        // 更新数据
        historicalData.value = histData.data;
        predictionData.value = predData.data;
        
        // 处理训练指标
        if (metricsDataRes.success && metricsDataRes.metrics) {
          metricsData.value = metricsDataRes.metrics;
          showMetrics.value = true;
        } else {
          console.warn('训练指标加载失败:', metricsDataRes.message);
          metricsData.value = null;
          showMetrics.value = false;
        }
        
        ElMessage.success(`${selectedProvince.value} 预测完成！`);
        
        // 更新图表
        nextTick(() => {
          renderChart();
        });

      } catch (error) {
        console.error('预测错误:', error);
        ElMessage.error('预测异常：' + error.message);
      } finally {
        predicting.value = false;
      }
    }

    const handleFileUpload = (file) => {
      const reader = new FileReader()
      reader.onload = (e) => {
        try {
          const content = e.target.result
          // 简单解析CSV文件（实际项目中可能需要更复杂的解析逻辑）
          const lines = content.split('\n')
          const headers = lines[0].split(',')
          
          // 检查列名
          if (!headers.includes('年份') && !headers.includes('year') || 
              !headers.includes('GDP') && !headers.includes('gdp')) {
            ElMessage.error('文件格式错误：必须包含年份和GDP两列')
            return
          }
          
          const yearIndex = headers.includes('年份') ? headers.indexOf('年份') : headers.indexOf('year')
          const gdpIndex = headers.includes('GDP') ? headers.indexOf('GDP') : headers.indexOf('gdp')
          
          const data = []
          for (let i = 1; i < lines.length; i++) {
            if (lines[i].trim() === '') continue
            
            const values = lines[i].split(',')
            if (values.length >= 2) {
              data.push({
                year: parseInt(values[yearIndex]),
                gdp: parseFloat(values[gdpIndex])
              })
            }
          }
          
          customData.value = data
          historicalData.value = data
          ElMessage.success('数据文件上传成功')
        } catch (error) {
          ElMessage.error('文件解析失败：' + error.message)
        }
      }
      reader.readAsText(file.raw)
    }

    // 修改自定义数据预测，调用后端API并传递省份信息
    const runCustomPrediction = async () => {
      if (!customData.value.length) {
        ElMessage.warning('请先上传数据文件')
        return
      }

      if (!selectedProvinceForCustom.value) {
        ElMessage.warning('请先选择省份以使用对应预测模型')
        return
      }

      predicting.value = true
      try {
        // 将自定义数据和选择的省份发送到后端进行预测
        const response = await fetch('/api/gdp/predict/custom', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            province: selectedProvinceForCustom.value,
            data: customData.value
          })
        })
        
        const result = await response.json()
        
        // 适配不同的API响应格式
        if ((result.code === 0 || result.success) && result.data) {
          predictionData.value = result.data
          ElMessage.success(`使用 ${selectedProvinceForCustom.value} 模型预测完成`)
          
          // 更新图表
          nextTick(() => {
            renderChart()
          })
        } else {
          ElMessage.error('预测失败：' + (result.message || '未知错误'))
        }
      } catch (error) {
        ElMessage.error('预测异常：' + error.message)
      } finally {
        predicting.value = false
      }
    }

    const formatNumber = (num) => {
      return new Intl.NumberFormat('zh-CN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(num)
    }

    const renderChart = () => {
      if (!hasData.value) return
      
      const chartDom = document.getElementById('gdp-chart')
      if (!chartDom) return
      
      if (chart) {
        chart.dispose()
      }
      
      chart = echarts.init(chartDom)
      
      // 准备图表数据
      const historicalYears = historicalData.value.map(d => d.year)
      const historicalGDP = historicalData.value.map(d => d.gdp)
      
      const predictionYears = predictionData.value.map(d => d.year)
      const predictionGDP = predictionData.value.map(d => d.gdp)
      
      const option = {
        tooltip: {
          trigger: 'axis',
          formatter: function(params) {
            let result = params[0].axisValue + '<br/>'
            params.forEach(param => {
              result += param.seriesName + ': ' + formatNumber(param.value) + ' 亿元<br/>'
            })
            return result
          }
        },
        legend: {
          data: ['历史GDP', '预测GDP']
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: [...historicalYears, ...predictionYears]
        },
        yAxis: {
          type: 'value',
          axisLabel: {
            formatter: function(value) {
              if (value >= 10000) {
                return (value / 10000).toFixed(1) + '万'
              }
              return value
            }
          }
        },
        series: [
          {
            name: '历史GDP',
            type: chartType.value,
            data: [...historicalGDP, ...Array(predictionYears.length).fill(null)],
            itemStyle: {
              color: '#5470c6'
            },
            lineStyle: {
              width: 3
            },
            markPoint: {
              data: [
                { type: 'max', name: '最大值' },
                { type: 'min', name: '最小值' }
              ]
            }
          },
          {
            name: '预测GDP',
            type: chartType.value,
            data: [...Array(historicalYears.length).fill(null), ...predictionGDP],
            itemStyle: {
              color: '#ee6666'
            },
            lineStyle: {
              width: 3,
              type: 'dashed'
            }
          }
        ]
      }
      
      chart.setOption(option)
      
      // 响应窗口大小变化
      window.addEventListener('resize', function() {
        chart.resize()
      })
    }

    const toggleChartType = () => {
      chartType.value = chartType.value === 'line' ? 'bar' : 'line'
      renderChart()
    }

    onMounted(() => {
      console.log('GDP预测组件已挂载')
      // 组件挂载时加载省份列表
      loadProvinces()
    })

    onUnmounted(() => {
      if (chart) {
        chart.dispose()
        chart = null
      }
    })

    return {
      selectedProvince,
      selectedProvinceForCustom,
      dataSource,
      loading,
      predicting,
      historicalData,
      predictionData,
      customData,
      chartType,
      provinces,
      hasData,
      statistics,
      handleDataSourceChange,
      handleProvinceChange,
      loadData,
      runPrediction,
      handleFileUpload,
      runCustomPrediction,
      formatNumber,
      toggleChartType,
      metricsData,
      showMetrics,
      formatMetricsForTable
    }
  }
}
</script>

<style scoped>
.gdp-prediction-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
  height: calc(100vh - 100px);
  overflow-y: auto;
  overflow-x: hidden;
}

.header-section {
  text-align: center;
  margin-bottom: 30px;
}

.header-section h2 {
  color: #303133;
  margin-bottom: 10px;
  font-size: 28px;
}

.description {
  color: #606266;
  font-size: 14px;
}

.control-section {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.control-content {
  padding: 10px 0;
}

.action-buttons {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.data-section {
  margin-bottom: 20px;
}

.data-card {
  height: 100%;
  min-height: 400px;
}

.prediction-value {
  font-weight: bold;
  color: #e6a23c;
}

.stats-section {
  margin-top: 20px;
}

.stat-item {
  text-align: center;
  padding: 20px;
}

.stat-title {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
}

.chart-section {
  margin-bottom: 20px;
}

.custom-data-preview {
  margin-top: 20px;
}

.custom-data-preview h4 {
  margin-bottom: 10px;
  color: #606266;
}

.mb-20 {
  margin-bottom: 20px;
}

.metrics-section {
  margin-top: 20px;
}

.info-box {
  background-color: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
  font-size: 14px;
}

.info-box p {
  margin: 8px 0;
  line-height: 1.6;
}

:deep(.el-table .cell) {
  text-align: center;
}

:deep(.success-row) {
  background-color: #f0f9ff !important;
}

:deep(.el-card__header) {
  padding: 12px 20px;
  border-bottom: 1px solid #ebeef5;
}

:deep(.el-upload) {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

:deep(.el-upload__tip) {
  margin-top: 10px;
  font-size: 12px;
  color: #909399;
}

/* 主容器滚动条样式 */
.gdp-prediction-container::-webkit-scrollbar {
  width: 10px;
}

.gdp-prediction-container::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 5px;
}

.gdp-prediction-container::-webkit-scrollbar-thumb {
  background: #409EFF;
  border-radius: 5px;
}

.gdp-prediction-container::-webkit-scrollbar-thumb:hover {
  background: #66b1ff;
}

/* 全局滚动条样式 */
:deep(::-webkit-scrollbar) {
  width: 8px;
  height: 8px;
}

:deep(::-webkit-scrollbar-track) {
  background: #f1f1f1;
  border-radius: 4px;
}

:deep(::-webkit-scrollbar-thumb) {
  background: #c1c1c1;
  border-radius: 4px;
}

:deep(::-webkit-scrollbar-thumb:hover) {
  background: #a8a8a8;
}

/* 确保所有滚动容器都有滚动条 */
:deep(.el-table__body-wrapper),
:deep(.el-card__body),
:deep(.el-main) {
  overflow: auto;
}
</style>

<style>
/* 全局样式，确保整个页面有滚动条 */
html, body {
  overflow: auto;
}

body {
  overflow-y: scroll;
}

/* 确保Element UI组件也有滚动条 */
.el-scrollbar__wrap {
  overflow: auto;
}
</style>