<template>
  <el-dialog
      :visible.sync="visible"
      title="新增内置软件"
      :before-close="handleClose"
      width="400px"
  >
    <el-form
        ref="softwareForm"
        :model="softwareForm"
        :rules="rules"
        label-width="120px"
    >
      <el-form-item label="软件名称" prop="name">
        <el-select
            v-model="softwareForm.name"
            placeholder="请选择软件名称"
            @change="handleNameChange"
        >
          <el-option
              v-for="(name, index) in Object.keys(supportedVersions)"
              :key="index"
              :label="name"
              :value="name"
          ></el-option>
        </el-select>
      </el-form-item>
      <el-form-item label="软件版本" prop="version">
        <el-select
            v-model="softwareForm.version"
            placeholder="请选择软件版本"
        >
          <el-option
              v-for="(version, index) in filteredVersions"
              :key="index"
              :label="version"
              :value="version"
          ></el-option>
        </el-select>
      </el-form-item>
      <el-form-item v-if="errorMessage" class="error-message">
        <span>{{ errorMessage }}</span>
      </el-form-item>
    </el-form>
    <div slot="footer" class="dialog-footer">
      <el-button @click="handleCancel">取消</el-button>
      <el-button type="primary" @click="handleConfirm">确定</el-button>
    </div>
  </el-dialog>
</template>

<script>
export default {
  name: 'AddSoftwareDialog',
  props: {
    visible: {
      type: Boolean,
      default: false
    },
    supportedVersions: {
      type: Object,
      required: true
    },
    packagesDepPython: {
      type: Array,
      required: true
    },
    existingSoftwares: {
      type: Array,
      required: true
    }
  },
  data() {
    return {
      softwareForm: {
        name: 'python',
        version: ''
      },
      rules: {
        name: [
          { required: true, message: '请选择软件名称', trigger: 'change' }
        ],
        version: [
          { required: true, message: '请选择软件版本', trigger: 'change' }
        ]
      },
      errorMessage: ''
    }
  },
  computed: {
    filteredVersions() {
      return this.supportedVersions[this.softwareForm.name] || []
    }
  },
  watch: {
    visible(newVal) {
      if (newVal) {
        this.$nextTick(() => {
          this.setDefaultVersion();
        });
      }
    },
    filteredVersions(newVal) {
      if (newVal.length > 0) {
        this.softwareForm.version = newVal[0];
      }
    }
  },
  methods: {
    handleNameChange() {
      this.errorMessage = '';
      this.setDefaultVersion();
    },
    setDefaultVersion() {
      if (this.filteredVersions.length > 0) {
        this.softwareForm.version = this.filteredVersions[0];
      }
    },
    resetForm() {
      this.$refs.softwareForm && this.$refs.softwareForm.resetFields();
      this.softwareForm.name = 'python';
      this.errorMessage = '';
      this.setDefaultVersion();
    },
    checkSoftwareExists() {
      return this.existingSoftwares.some(
          software => software.name === this.softwareForm.name
      );
    },
    handleConfirm() {
      this.$refs.softwareForm.validate(valid => {
        if (valid) {
          if (this.checkSoftwareExists()) {
            this.errorMessage = '错误！已添加该软件，不要重复添加。';
            return;
          }

          if (this.packagesDepPython.includes(this.softwareForm.name)) {
            const hasPython = this.existingSoftwares.some(
                software => software.name === 'python'
            );

            if (!hasPython) {
              this.errorMessage = '错误！请先添加依赖的python。';
              return;
            }
          }

          this.$emit('confirm', { ...this.softwareForm });
          this.handleClose();
        }
      });
    },
    handleCancel() {
      this.$emit('cancel');
      this.handleClose();
    },
    handleClose() {
      this.resetForm();
      this.$emit('update:visible', false);
    }
  },
  mounted() {
    if (this.visible) {
      this.setDefaultVersion();
    }
  }
}
</script>

<style scoped>
.error-message {
  margin-bottom: 0;
}
.error-message span {
  color: #F56C6C;
  font-size: 12px;
}
</style>
