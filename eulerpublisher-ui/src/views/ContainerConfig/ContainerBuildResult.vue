<template>
  <div class="build-result-page">
    <div class="build-header">
      <h1>容器构建结果（id: {{id}}）</h1>
      <el-button
          icon="el-icon-refresh"
          type="primary"
          @click="fetchBuildResult"
      >
        刷新
      </el-button>
    </div>

    <el-card shadow="hover" class="info-card">
      <h2>1.基本信息</h2>
      <el-table :data="generalInfoData" border style="width: 100%;" :show-header="false">
        <el-table-column
            prop="label"
            label="Label"
            width="150">
        </el-table-column>
        <el-table-column
            prop="value"
            label="Value">
          <template slot-scope="scope">
            <span v-if="scope.row.label === '构建状态'" :class="scope.row.value.includes('失败') ? 'status-failed' : ''">
              {{ scope.row.value }}
            </span>
            <span v-else>
              {{ scope.row.value }}
            </span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card shadow="hover" class="info-card" style="margin-top: 20px;" >
      <h2>2.构建结果</h2>
      <el-table :data="resultsData" border style="width: 100%;" :show-header="false">
        <el-table-column
            prop="label"
            label="Label"
            width="150">
        </el-table-column>
        <el-table-column
            prop="value"
            label="Value">
          <template slot-scope="scope">
            <span v-if="scope.row.label === '构建状态' && scope.row.value === '失败'" class="status-failed">
              {{ scope.row.value }}
            </span>
            <template v-else-if="scope.row.label === 'GitHub Actions URL'">
              <span v-if="scope.row.url">
                <a
                    :href=scope.row.url
                    target="_blank"
                    class="log-link"
                >
                    {{ scope.row.value }}
                  </a>
              </span>
              <span v-else>
                {{ scope.row.value }}
              </span>
            </template>
            <span v-else>
              {{ scope.row.value }}
            </span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script>
import {mapActions, mapGetters} from "vuex";
import {formatTimestamp, calculateBuildTime} from '@/utils/date';
import {queryBuild} from "@/api/container"

export default {
  props: {
    id: {
      type: [Number],
      required: true
    }
  },
  data() {
    return {

    }
  },
  computed: {
    ...mapGetters(["getContainerBuildResult"]),

    generalInfoData() {
      if (!this.getContainerBuildResult) return []
      const res = this.getContainerBuildResult
      return [
        { label: '构建状态', value: this.formatState(res.status) },
        {
          label: '提交时间',
          value: res.submitted_on ? formatTimestamp(res.submitted_on) : '未提交'
        },
        {
          label: '开始时间',
          value: res.started_on ? formatTimestamp(res.started_on) : '未开始'
        },
        {
          label: '结束时间',
          value: res.ended_on ? formatTimestamp(res.ended_on) : '未结束'
        },
        {
          label: '构建耗时',
          value: res.started_on && res.ended_on ? calculateBuildTime(res.started_on, res.ended_on) : '-'
        }
      ]
    },

    resultsData() {
      if (!this.getContainerBuildResult) return []
      const res = this.getContainerBuildResult
      return [
        {
          label: '构建状态',
          value:  this.formatState(res.status)
        },
        {
          label: 'GitHub Actions URL',
          value: res.run_id !== -1 ? this.getUrl(res.owner_name, res.repo_name, res.run_id) : '-',
          url: res.run_id !== -1 ? this.getUrl(res.owner_name, res.repo_name, res.run_id) : null
        }
      ]
    },
  },
  created() {
    this.fetchBuildResult()
  },
  methods: {
    ...mapActions(['setContainerBuildResult']),
    fetchBuildResult() {
      console.log('in fetchBuildResult, id:', this.id)
      queryBuild(this.id).then(res => {
        if (res.status === 'success') {
          this.setContainerBuildResult(res.data)
        }
      })
      .catch(error => {
        console.error('获取构建结果失败', error);
        this.$message.error('获取构建结果失败，请重试');
      });
    },
    formatState(state) {
      const stateMap = {
        pending: '待处理',
        uploading: '工作流文件上传中',
        waiting_running: '等待运行',
        running: '运行中',
        succeeded: '成功',
        failed: '失败',

      };
      return stateMap[state] || state;
    },
    getUrl(owner_name, repo_name, run_id) {
      return `https://github.com/${owner_name}/${repo_name}/actions/runs/${run_id}`
    }
  }
}
</script>

<style scoped>
.build-result-page {
  width: 80%;
  margin: 20px auto;
}
.build-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.info-card {
  padding: 15px;
}
.status-failed {
  color: #f56c6c;
}
.log-link {
  color: #409eff;
  text-decoration: none;
}
.log-link:hover {
  text-decoration: underline;
}
</style>