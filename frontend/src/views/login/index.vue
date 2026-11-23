<template>
  <div class="login-page">
    <div class="login-page__bg-glow login-page__bg-glow--1" />
    <div class="login-page__bg-glow login-page__bg-glow--2" />

    <div class="login-card">
      <div class="login-card__brand">
        <el-icon class="login-card__logo"><ShoppingCart /></el-icon>
        <h1 class="login-card__title">订单汇聚管理系统</h1>
        <p class="login-card__subtitle">多平台 · 多店铺 · 一站式订单运营</p>
      </div>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        class="login-form"
        size="large"
        @keyup.enter="handleSubmit"
      >
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="请输入账号" :prefix-icon="User" clearable />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" class="login-form__submit" :loading="loading" @click="handleSubmit">
            登 录
          </el-button>
        </el-form-item>
      </el-form>

      <p class="login-card__tip">默认管理员：admin / 123456</p>
    </div>
  </div>
</template>

<script setup lang="ts">
// 登录页
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { User, Lock, ShoppingCart } from '@element-plus/icons-vue'
import { useUserStore } from '@/store/user'
import type { LoginParams } from '@/types/system'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const formRef = ref<FormInstance>()
const loading = ref(false)
const form = reactive<LoginParams>({ username: '', password: '' })

const rules: FormRules<LoginParams> = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function handleSubmit() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      await userStore.login({ ...form })
      await userStore.fetchUserInfo()
      ElMessage.success('登录成功')
      const redirect = (route.query.redirect as string) || '/dashboard/overview'
      router.replace(redirect)
    } catch {
      // 错误提示已由请求层统一处理
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped lang="scss">
.login-page {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100vh;
  overflow: hidden;
  background: linear-gradient(135deg, #312e81 0%, #1e293b 60%, #0f172a 100%);

  &__bg-glow {
    position: absolute;
    border-radius: 50%;
    filter: blur(90px);
    opacity: 0.5;

    &--1 {
      width: 460px;
      height: 460px;
      background: var(--color-primary);
      top: -120px;
      left: -80px;
    }

    &--2 {
      width: 420px;
      height: 420px;
      background: var(--color-info);
      bottom: -140px;
      right: -60px;
    }
  }
}

.login-card {
  position: relative;
  z-index: 1;
  width: 400px;
  padding: 40px 36px;
  background: rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: var(--radius-lg);
  box-shadow: 0 16px 48px rgba(15, 23, 42, 0.35);

  &__brand {
    text-align: center;
    margin-bottom: 28px;
  }

  &__logo {
    font-size: 40px;
    color: var(--color-primary-hover);
  }

  &__title {
    margin: 12px 0 6px;
    font-size: 22px;
    font-weight: 700;
    color: #fff;
    letter-spacing: 1px;
  }

  &__subtitle {
    margin: 0;
    font-size: 13px;
    color: rgba(226, 232, 240, 0.7);
  }

  &__tip {
    margin: 4px 0 0;
    text-align: center;
    font-size: 12px;
    color: rgba(226, 232, 240, 0.55);
  }
}

.login-form {
  :deep(.el-input__wrapper) {
    background: rgba(255, 255, 255, 0.9);
  }

  &__submit {
    width: 100%;
    letter-spacing: 4px;
    font-weight: 600;
  }
}
</style>
