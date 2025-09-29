<template>
  <div class="config-container">
    <el-card class="config-card" shadow="hover">
      <h3>1.容器镜像配置</h3>
      <el-form :model="containerForm" :rules="containerRules" label-width="120px" ref="containerFormRef">
        <el-form-item label="openEuler版本" prop="version">
          <el-select
              v-model="containerForm.version"
              placeholder="请选择openEuler版本"
              style="width: 100%;"
          >
            <el-option label="25.03" value="25.03"></el-option>
            <el-option label="24.09" value="24.09"></el-option>
            <el-option label="24.03_LTS_SP2" value="24.03_LTS_SP2"></el-option>
            <el-option label="24.03_LTS_SP1" value="24.03_LTS_SP1"></el-option>
            <el-option label="22.03_LTS_SP3" value="22.03_LTS_SP3"></el-option>
            <el-option label="22.03_LTS_SP2" value="22.03_LTS_SP2"></el-option>
            <el-option label="22.03_LTS_SP1" value="22.03_LTS_SP1"></el-option>
            <el-option label="22.03_LTS" value="22.03_LTS"></el-option>
            <el-option label="20.03_LTS_SP4" value="20.03_LTS_SP4"></el-option>
            <el-option label="20.03_LTS_SP3" value="20.03_LTS_SP3"></el-option>
            <el-option label="20.03_LTS_SP1" value="20.03_LTS_SP1"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="目标架构" prop="arch">
          <el-checkbox-group v-model="containerForm.arch" placeholder="请选择">
            <el-checkbox label="x86_64" name="arch"></el-checkbox>
            <el-checkbox label="aarch64" name="arch"></el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="内置软件">
          <el-table :data="containerForm.softwares" border style="width: 100%">
            <el-table-column prop="name" label="软件名称"></el-table-column>
            <el-table-column prop="version" label="软件版本"></el-table-column>
            <el-table-column label="操作">
              <template slot-scope="scope">
                <el-button
                    size="mini"
                    type="primary"
                    @click="handleEditSoftware(scope.row)"
                >编辑</el-button>
                <el-button
                    size="mini"
                    type="danger"
                    @click="handleDeleteSoftware(scope.$index)"
                >删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div style="margin-top: 10px">
            <el-button type="success" @click="showAddDialog = true">新增</el-button>
            <el-button type="warning" @click="handleClearSoftwares">清空</el-button>
          </div>
        </el-form-item>
      </el-form>
    </el-card>
    <el-card class="config-card" shadow="hover" style="margin-top: 20px;">
      <h3>2.推送仓库配置</h3>
      <el-form
          ref="pushForm"
          :model="pushForm"
          :rules="pushRules"
          label-width="120px"
      >
        <el-form-item label="推送目标" prop="registry">
          <el-checkbox-group v-model="pushForm.registry" placeholder="请选择">
            <el-checkbox label="docker.io" name="registry"></el-checkbox>
            <el-checkbox label="quay.io" name="registry"></el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>
    </el-card>
    <el-button
        type="primary"
        style="margin-top: 20px;"
        @click="handleSubmit"
    >
      启动构建
    </el-button>

    <add-software-dialog
        :visible.sync="showAddDialog"
        :supported-versions="SUPPORTED_VERSIONS"
        :packages-dep-python="PACKAGES_DEP_PYTHON"
        :existing-softwares="containerForm.softwares"
        @confirm="handleAddConfirm"
    />

    <edit-software-dialog
        :visible.sync="showEditDialog"
        :supported-versions="SUPPORTED_VERSIONS"
        :software="currentSoftware"
        @confirm="handleEditConfirm"
    />
  </div>
</template>

<script>
import AddSoftwareDialog from './AddSoftwareDialog.vue'
import EditSoftwareDialog from './EditSoftwareDialog.vue'
import {containerBuild} from "@/api/container";

export default {
  name: 'ContainerConfig',
  components: {
    AddSoftwareDialog,
    EditSoftwareDialog
  },
  data() {
    return {
      containerForm: {
        version: '22.03_LTS',
        arch: ['x86_64'],
        softwares: [{ name: 'python', version: '3.11.1' }],
      },
      pushForm: {
        registry: ['docker.io']
      },
      containerRules: {
        version: [
          { required: true, message: '请选择一个版本', trigger: 'change' }
        ],
        arch: [
          { type: 'array', required: true, message: '请至少选择一个架构', trigger: 'change' }
        ]
      },
      pushRules: {
        registry: [
          { type: 'array', required: true, message: '请至少选择一个推送目标', trigger: 'change' },
        ],
      },
      showAddDialog: false,
      showEditDialog: false,
      currentSoftware: null,
      SUPPORTED_VERSIONS: {
        "cann": ["8.1.RC1", "8.0.0", "8.0.RC3", "8.0.RC2", "8.0.RC1"],
        "python": ["3.9.1", "3.10.1", "3.11.1"],
        "pytorch": ["2.4.1", "2.5.0", "2.6.0"]
      },
      PACKAGES_DEP_PYTHON: ["cann", "pytorch"]
    };
  },
  methods: {
    handleAddConfirm(software) {
      this.containerForm.softwares.push(software)
      this.showAddDialog = false
    },
    handleEditSoftware(row) {
      this.currentSoftware = { ...row }
      this.showEditDialog = true
    },
    handleEditConfirm(updatedSoftware) {
      const index = this.containerForm.softwares.findIndex(
          item => item.name === updatedSoftware.name
      )
      if (index !== -1) {
        this.containerForm.softwares.splice(index, 1, updatedSoftware)
      }
      this.showEditDialog = false
      this.currentSoftware = null
    },
    handleDeleteSoftware(index) {
      this.containerForm.softwares.splice(index, 1);
    },
    handleClearSoftwares() {
      this.containerForm.softwares = [];
    },
    handleSubmit() {
      this.$refs.containerFormRef.validate((valid) => {
        if (valid) {
          const data = {
              archs: [...this.containerForm.arch],
              registries: [...this.pushForm.registry],
              layers: [
                {
                  name: 'openeuler',
                  version: this.containerForm.version
                },
                ...this.containerForm.softwares.map(software => ({
                  name: software.name,
                  version: software.version
                }))
              ]

          }
          containerBuild(data)
              .then(response => {
                const resdata = response.data
                this.$router.push({
                  name: "ContainerBuildResult",
                  params:{
                    id: resdata.id
                  }

                });
              })
              .catch(error => {
                this.$message.error('启动构建失败，请重试');
              });
        } else {
          this.$message.error('表单验证失败');
          return false;
        }
      });
    },
  },
};
</script>

<style scoped>
.config-container {
  width: 80%;
  margin: 0 auto;
  padding: 20px;
}
.config-card {
  width: 100%;
}
</style>
