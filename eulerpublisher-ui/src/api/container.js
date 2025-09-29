import { request } from '@/utils/request'

export function containerBuild(data) {
    return request({
        url: '/container/build',
        method: 'post',
        data: data
    })
}

export function queryBuild(id) {
    return request({
        url: '/workflow/status/' + id,
        method: 'get'
    })
}