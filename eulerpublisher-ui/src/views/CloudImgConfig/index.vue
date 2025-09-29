<template>
  <div class="config-container">
    <!-- cloud image config card -->
    <el-card class="config-card" shadow="hover">
      <h3>1.云镜像配置</h3>
      <el-form :model="cloudImgForm" :rules="rules" label-width="120px" ref="projectFormRef">
        <el-form-item label="openEuler版本" prop="version">
          <el-checkbox-group v-model="cloudImgForm.version" placeholder="请选择">
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
          <el-checkbox-group v-model="cloudImgForm.arch" placeholder="请选择">
            <el-checkbox label="x86_64" name="arch"></el-checkbox>
            <el-checkbox label="aarch64" name="arch"></el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>
    </el-card>


    <el-card class="config-card" shadow="hover" style="margin-top: 20px;">
      <h3>2.公有云配置</h3>
      <el-form
          :model="cloudImgForm"
          :rules="rules"
          ref="cloudImgFormRef"
          label-width="120px"
      >
        <el-form-item label="推送目标" prop="pushTarget">
          <el-select v-model="cloudImgForm.pushTarget" placeholder="请选择">
            <el-option label="华为云" value="huawei"></el-option>
            <el-option label="阿里云" value="ali"></el-option>
            <el-option label="腾讯云" value="tencent"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="选择配置" prop="selectConfig">
          <el-select v-model="cloudImgForm.selectConfig" placeholder="请选择">
            <el-option label="标准配置" value="standard"></el-option>
            <el-option label="最小配置" value="minimum"></el-option>
            <el-option label="自定义配置" value="custom"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="地域" prop="region">
          <el-select v-model="cloudImgForm.region" placeholder="请选择">
            <el-option label="华北-北京" value="beijing"></el-option>
            <el-option label="华东-上海" value="shanghai"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="存储桶" prop="bucket">
          <el-select v-model="cloudImgForm.bucket" placeholder="请选择">
            <el-option label="bucket-01" value="bucket-01"></el-option>
            <el-option label="bucket-02" value="bucket-02"></el-option>
            <el-option label="bucket-03" value="bucket-03"></el-option>
          </el-select>
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
  </div>
</template>

<script>
export default {
  name: 'CloudImg',
  data() {
    return {
      cloudImgForm: {
        version: ['22.03_LTS'],
        arch: ['x86_64'],
        pushTarget: '',
        selectConfig: '',
        region: '',
        bucket: ''
      },

      rules: {
        version: [
          {type: 'array', required: true, message: '请至少选择一个版本', trigger: 'change' }
        ],
        arch: [
          {type: 'array', required: true, message: '请至少选择一个架构', trigger: 'change' }
        ],
        pushTarget: [
          { required: true, message: '请选择推送目标', trigger: 'change' }
        ],
        selectConfig: [
          { required: true, message: '请选择配置', trigger: 'change' }
        ],
        region: [
          { required: true, message: '请选择地域', trigger: 'change' }
        ],
        bucket: [
          { required: true, message: '请选择存储桶', trigger: 'change' }
        ]
      }
    };
  },
  methods: {
    handleSubmit() {
      this.$refs.cloudImgFormRef.validate((valid) => {
        if (valid) {
          this.startBuild();
        } else {
          this.$message.error('请完善所有必填项');
          return false;
        }
      });
    },
    startBuild() {
      this.$message.success('构建已启动，正在处理中...');
      console.log('构建参数:', this.cloudImgForm);
    }
  }
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
