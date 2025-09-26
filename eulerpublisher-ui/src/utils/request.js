import axios from 'axios'
import { Loading, Message } from 'element-ui'

const service = axios.create({
    baseURL: process.env.VUE_APP_BASE_API,
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json'
    }
})

let loadingInstance = null

service.interceptors.request.use(
    config => {
        loadingInstance = Loading.service({
            lock: true,
            text: '处理中，请稍候...',
            background: 'rgba(0, 0, 0, 0.5)'
        })

        if (config.data) {
            config.data = {
                meta: {
                    timestamp: new Date().getTime()
                },
                data: config.data
            }
        }

        return config
    },
    error => {
        if (loadingInstance) {
            loadingInstance.close()
        }
        Message.error('请求发送失败，请重试')
        return Promise.reject(error)
    }
)

service.interceptors.response.use(
    response => {
        if (loadingInstance) {
            loadingInstance.close()
        }
        return response.data
    },
    error => {
        if (loadingInstance) {
            loadingInstance.close()
        }
        return Promise.reject(error)
    }
)

export function request(options) {
    return service(options)
}

export default service
