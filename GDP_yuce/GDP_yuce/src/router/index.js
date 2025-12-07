import {createRouter, createWebHistory} from 'vue-router'

const routes = [
    {
        path: '/',
        component: () => import('../components/Layout.vue'), // 使用布局组件
        redirect: '/map',
        children: [
            {
                path: '/map',
                name: 'Map',
                component: () => import('../components/Map.vue')
            },
            {
                path: '/comparison',
                name: 'Comparison',
                component: () => import('../components/comparison.vue')
            },
            {
                path: '/heatmap',
                name: 'Heatmap',
                component: () => import('../components/Heatmap.vue')
            },
            {
                path: '/population',
                name: 'Population',
                component: () => import('../components/Population.vue') 
            },
            {
                path:'/predict',
                name:'Predict',
                component: () => import('../components/Predict.vue')
            }
        ]
    },
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

export default router