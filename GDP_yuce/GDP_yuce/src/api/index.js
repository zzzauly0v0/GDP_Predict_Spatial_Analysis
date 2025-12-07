import request from '../utils/request'

export const getPopulationData = () => {
  return request.get('/人口数据') 
}

export const getFinancialExpenditureData = () => {
  return request.get('/地方财政支出数据') 
}

export const getQuarterlyData = () => {
  return request.get('/季度数据')
}

export const getQuarterlyIndexData = () => {
  return request.get('/季度指数数据') 
}

export const getAnnualData = () => {
  return request.get('/年度数据') 
}

export const getConsumerGoodsData = () => {
  return request.get('/消费品数据') 
}

// GDP空间分析API
export const getSpatialAnalysisData = (year) => {
  return request.get(`/spatial/data/${year}`)
}

export const getSpatialAvailableYears = () => {
  return request.get('/spatial/available-years')
}

export const getSpatialYearStats = (year) => {
  return request.get(`/spatial/stats/${year}`)
}

export const refreshSpatialData = () => {
  return request.post('/spatial/refresh')
}

//GDP预测API
export const getGDPHistoricalData = (province) => {
  return request.get(`/gdp/historical/${encodeURIComponent(province)}`)
}

export const getGDPPrediction = (province) => {
  return request.get(`/gdp/predict/${encodeURIComponent(province)}`)
}

export const getGDPMetrics = (province) => {
  return request.get(`/gdp/metrics/${encodeURIComponent(province)}`)
}