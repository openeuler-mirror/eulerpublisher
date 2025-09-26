import { request } from '@/utils/request'

export function rpmBuild(data) {
    return request({
        url: '/rpm/build',
        method: 'post',
        data: data
    })
}

export function queryBuild(id) {
    return request({
        url: '/rpm/build/' + id,
        method: 'get'
    })
}