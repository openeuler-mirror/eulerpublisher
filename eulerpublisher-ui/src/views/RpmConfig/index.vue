<template>
  <div class="config-container">
    <el-card class="config-card" shadow="hover">
      <h3>1.项目配置</h3>
      <el-form :model="projectForm" :rules="projectRules" label-width="120px" ref="projectFormRef">
        <el-form-item label="项目名称" prop="name">
          <el-input v-model="projectForm.name"></el-input>
        </el-form-item>
        <el-form-item label="openEuler版本" prop="version">
          <el-checkbox-group v-model="projectForm.version" placeholder="请选择">
            <el-checkbox label="25.03" name="version"></el-checkbox>
            <el-checkbox label="24.09" name="version"></el-checkbox>
            <el-checkbox label="24.03_LTS_SP2" name="version"></el-checkbox>
            <el-checkbox label="24.03_LTS_SP1" name="version"></el-checkbox>
            <el-checkbox label="22.03_LTS_SP3" name="version"></el-checkbox>
            <el-checkbox label="22.03_LTS_SP2" name="version"></el-checkbox>
            <el-checkbox label="22.03_LTS_SP1" name="version"></el-checkbox>
            <el-checkbox label="22.03_LTS" name="version"></el-checkbox>
            <el-checkbox label="20.03_LTS_SP4" name="version"></el-checkbox>
            <el-checkbox label="20.03_LTS_SP3" name="version"></el-checkbox>
            <el-checkbox label="20.03_LTS_SP1" name="version"></el-checkbox>
            </el-checkbox-group>
        </el-form-item>
        <el-form-item label="目标架构" prop="arch">
          <el-checkbox-group v-model="projectForm.arch" placeholder="请选择">
            <el-checkbox label="x86_64" name="arch"></el-checkbox>
            <el-checkbox label="aarch64" name="arch"></el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="config-card" shadow="hover" style="margin-top: 20px;">
      <h3>2.软件包配置</h3>
      <el-tabs v-model="activeTab">
        <el-tab-pane label="SCM" name="scm">
          <el-form :model="scmForm" :rules="scmFormRules" label-width="120px" ref="scmFormRef">
            <el-form-item label="Git URL" prop="gitUrl">
              <el-input v-model="scmForm.gitUrl"></el-input>
            </el-form-item>
            <el-form-item label="分支" prop="branch">
              <el-input v-model="scmForm.branch"></el-input>
            </el-form-item>
            <el-form-item label="子目录" prop="subDir">
              <el-input v-model="scmForm.subDir" placeholder="源代码和.spec文件所在的目录"></el-input>
            </el-form-item>
            <el-form-item label="spec文件路径" prop="specPath">
              <el-input v-model="scmForm.specPath" placeholder=".spec文件在子目录中的路径"></el-input>
            </el-form-item>
          </el-form>
        </el-tab-pane>
        <el-tab-pane label="PyPI" name="pypi">
          <el-form :model="pypiForm" :rules="pypiFormRules" label-width="120px" ref="pypiFormRef">
            <el-form-item label="PyPI包名" prop="pypiName">
              <el-input v-model="pypiForm.pypiName" ></el-input>
            </el-form-item>
            <el-form-item label="PyPI包版本" prop="pypiVersion">
              <el-input v-model="pypiForm.pypiVersion" ></el-input>
            </el-form-item>
          </el-form>
        </el-tab-pane>
        <el-tab-pane label="RubyGems" name="rubygems">
          <el-form :model="rubygemsForm" :rules="rubygemsRules" ref="rubygemsFormRef" label-width="120px">
            <el-form-item label="Gem包名" prop="gemName">
              <el-input v-model="rubygemsForm.gemName"></el-input>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>

    </el-card>

    <el-button type="primary" style="margin-top: 20px;" @click="handleClick">启动构建</el-button>
  </div>
</template>

<script>
import {rpmBuild} from "@/api/rpm";
import { mapActions } from "vuex";

export default {
  data() {
    return {
      projectForm: {
        name: 'test',
        version: ['22.03_LTS'],
        arch: ['x86_64'],
      },
      scmForm: {
        // packageName: '',
        gitUrl: 'https://gitee.com/Kirin2003/ethtool',
        branch: 'master',
        subDir: '',
        specPath: ''
      },
      projectRules: {
        name: [
          {required: true, message: '请输入项目名称', trigger: 'blur' }
        ],
        version: [
          {type: 'array', required: true, message: '请至少选择一个版本', trigger: 'change' }
        ],
        arch: [
          {type: 'array', required: true, message: '请至少选择一个架构', trigger: 'change' }
        ],
      },
      scmFormRules: {
        gitUrl: [
          {required: true, message: '请输入Git URL', trigger: 'blur' }
        ],
        branch: [
          {message: '请输入分支', trigger: 'change' }
        ],
        subDir: [
          {message: '请输入源代码和.spec文件所在的目录', trigger: 'change' }
        ],
        specPath: [
          {message: '请输入.spec文件在子目录中的路径', trigger: 'change' }
        ],
      },
      pypiForm: {
        pypiName: 'oic',
        pypiVersion: ''
      },
      pypiFormRules: {
        pypiName: [
          { required: true, message: '请输入PyPI包名', trigger: 'blur' }
        ],
        pypiVersion: [],
      },
      rubygemsForm: {
        gemName: 'mongo'
      },
      rubygemsRules: {
        gemName: [
          { required: true, message: '请输入 Gem 包名', trigger: 'blur' },
        ]
      },
      activeTab: 'scm'
    };
  },
  methods: {
    ...mapActions(["setBuildResult"]),
    handleClick() {
      this.$refs['projectFormRef'].validate((projectValid) => {
        if (projectValid) {
          if (this.activeTab === 'scm') {
            this.$refs['scmFormRef'].validate((scmValid) => {
              if (scmValid) {
                const data = {
                  repo_type: 'scm',
                  project: this.projectForm.name,
                  version: this.projectForm.version,
                  arch: this.projectForm.arch,
                  ...this.scmForm
                };
                rpmBuild(data)
                    .then(response => {
                      const resdata = response.data

                      this.$router.push({
                        name: "RpmBuildResult",
                        params:{
                          id: resdata.id
                        }

                      });
                    })
                    .catch(error => {
                      this.$message.error('启动构建失败，请重试');
                    });
              } else {
                this.$message.error('SCM 表单验证失败');
              }
            });
          } else if (this.activeTab === 'pypi') {
            this.$refs['pypiFormRef'].validate((pypiValid) => {
              if (pypiValid) {
                const data = {
                  repo_type: 'pypi',
                  project: this.projectForm.name,
                  version: this.projectForm.version,
                  arch: this.projectForm.arch,
                  ...this.pypiForm
                };
                rpmBuild(data)
                    .then(response => {
                      const resdata = response.data

                      this.$router.push({
                        name: "RpmBuildResult",
                        params:{
                          id: resdata.id
                        }

                      });
                    })
                    .catch(error => {
                      this.$message.error('启动构建失败，请重试');
                    });
              } else {
                this.$message.error('PyPI 表单验证失败');
              }
            });
          } else if (this.activeTab === 'rubygems') {
            this.$refs['rubygemsFormRef'].validate((rubygemsValid) => {
              if (rubygemsValid) {
                const data = {
                  repo_type: 'rubygems',
                  project: this.projectForm.name,
                  version: this.projectForm.version,
                  arch: this.projectForm.arch,
                  ...this.rubygemsForm
                };
                rpmBuild(data)
                    .then(response => {
                      const resdata = response.data

                      this.$router.push({
                        name: "RpmBuildResult",
                        params:{
                          id: resdata.id
                        }

                      });
                    })
                    .catch(error => {
                      this.$message.error('启动构建失败，请重试');
                    });
              } else {
                this.$message.error('RubyGems 表单验证失败');
              }
            });
          }
        } else {
          this.$message.error('项目配置表单验证失败');
        }
      });
    }
  }
}
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