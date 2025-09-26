<template>
  <div class="build-result-page">
    <div class="build-header">
      <h1>软件包构建结果（id: {{id}}）</h1>
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
      <h2>2.源数据</h2>
      <el-table :data="sourceData" border style="width: 100%;" :show-header="false">
        <el-table-column
            prop="label"
            label="Label"
            width="150">
        </el-table-column>
        <el-table-column
            prop="value"
            label="Value">
        </el-table-column>
      </el-table>
    </el-card>

    <el-card shadow="hover" class="info-card" style="margin-top: 20px;" >
      <h2>3.构建结果</h2>
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
            <template v-else-if="scope.row.label === '构建日志'">
              <template v-if="['running', 'succeeded', 'failed'].includes(scope.row.state)">
                <span v-for="(logFile, index) in splitLogFiles(scope.row.value)" :key="index">
                  <a
                      :href="getLogUrl(scope.row.buildBaseUrl, logFile)"
                      target="_blank"
                      class="log-link"
                  >
                    {{ logFile }}
                  </a>
                  <span v-if="index < splitLogFiles(scope.row.value).length - 1"> , </span>
                </span>
              </template>
              <template v-else>
                <span>-</span>
              </template>

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
import {queryBuild} from "@/api/rpm"

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
    ...mapGetters(["getRpmBuildResult"]),

    generalInfoData() {
      if (!this.getRpmBuildResult) return []
      const res = this.getRpmBuildResult
      return [
        { label: '构建状态', value: this.formatState(res.state) },
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
        },
        {
          label: '目录',
          value: res.project_dirname
        },
        {
          label: '提交人',
          value: res.submitter
        }
      ]
    },

    sourceData() {
      if (!this.getRpmBuildResult) return []
      const res = this.getRpmBuildResult
      return [
        {
          label: '包名',
          value: res.source_package.name ? res.source_package.name : '-'
        },
        {
          label: '版本',
          value: res.source_package.version ? res.source_package.version : '-'
        }
      ]
    },

    resultsData() {
      if (!this.getRpmBuildResult) return []
      const res = this.getRpmBuildResult
      return [
        {
          label: '构建状态',
          value:  this.formatState(res.state)
        },
        {
          label: '构建日志',
          value: 'builder-live.log.gz, backend.log.gz',
          buildBaseUrl: this.getBuildBaseUrl(res.ownername, res.project_dirname, res.id),
          state: res.state
        }
      ]
    },
  },
  created() {
    this.fetchBuildResult()
  },
  methods: {
    ...mapActions(['setRpmBuildResult']),
    fetchBuildResult() {
      queryBuild(this.id).then(res => {
        if (res.status === 'success') {
          this.setRpmBuildResult(res.data)
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
        importing: '导入中',
        running: '运行中',
        succeeded: '成功',
        failed: '失败'
      };
      return stateMap[state] || state;
    },
    splitLogFiles(logString) {
      if (!logString) return [];
      return logString.split(',').map(file => file.trim());
    },

    getLogUrl(baseUrl, fileName) {
      return `${baseUrl}${fileName}`;
    },
    getBuildBaseUrl(owner, project, id) {
      const paddedId = String(id).padStart(8, '0')
      return `https://eur.openeuler.openatom.cn/results/${owner}/${project}/srpm-builds/${paddedId}/`
    },
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