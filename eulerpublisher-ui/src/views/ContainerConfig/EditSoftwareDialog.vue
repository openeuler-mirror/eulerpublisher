<template>
  <el-dialog
      :visible.sync="visible"
      title="编辑软件版本"
      :before-close="handleClose"
      width="400px"
  >
    <el-form
        ref="editForm"
        :model="editForm"
        :rules="rules"
        label-width="120px"
    >
      <el-form-item label="软件名称">
        <el-input
            v-model="editForm.name"
            disabled
            placeholder="软件名称"
            class="form-control"
            readonly
        ></el-input>
      </el-form-item>

      <el-form-item label="软件版本" prop="version">
        <el-select
            v-model="editForm.version"
            placeholder="请选择软件版本"
            class="form-control"
        >
          <el-option
              v-for="(version, index) in filteredVersions"
              :key="index"
              :label="version"
              :value="version"
          ></el-option>
        </el-select>
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
  name: 'EditSoftwareDialog',
  props: {
    visible: {
      type: Boolean,
      default: false
    },
    supportedVersions: {
      type: Object,
      required: true
    },
    software: {
      type: Object,
      required: true,
      default: () => ({ name: '', version: '' })
    }
  },
  data() {
    return {
      editForm: {
        name: '',
        version: ''
      },
      rules: {
        version: [
          { required: true, message: '请选择软件版本', trigger: 'change' }
        ]
      }
    }
  },
  computed: {
    filteredVersions() {
      return this.supportedVersions[this.editForm.name] || []
    }
  },
  watch: {
    visible(newVal) {
      if (newVal) {
        this.initializeForm()
      }
    },
    software: {
      handler(newVal) {
        if (this.visible) {
          this.initializeForm()
        }
      },
      deep: true
    }
  },
  methods: {
    initializeForm() {
      this.editForm = {
        name: this.software.name || '',
        version: this.software.version || ''
      }
    },
    handleConfirm() {
      this.$refs.editForm.validate(valid => {
        if (valid) {
          this.$emit('confirm', { ...this.editForm })
          this.handleClose()
        }
      })
    },
    handleCancel() {
      this.$emit('cancel')
      this.handleClose()
    },
    handleClose() {
      this.$emit('update:visible', false)
    }
  }
}
</script>

<style scoped>
.dialog-footer {
  text-align: right;
}

.form-control {
  width: 100%;
  box-sizing: border-box;
}

::v-deep .el-input.is-disabled .el-input__inner {
  background-color: #f5f7fa;
  color: #606266;
  cursor: not-allowed;
}

::v-deep .el-input.is-disabled .el-input__inner:focus {
  box-shadow: none;
}
</style>
