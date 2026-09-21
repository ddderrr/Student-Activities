<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useLanguage } from '../../composables/useLanguage'

import {
  GraduationCap,
  BriefcaseBusiness,
  LockKeyhole,
  Eye,
  EyeOff,
  ArrowRight,
  Undo2
} from 'lucide-vue-next'

const router = useRouter()
const { t } = useLanguage()

const username = ref('')
const password = ref('')
const rememberMe = ref(false)
const showPassword = ref(false)

/*
  MOCK ADMIN LOGIN
  ยังไม่ตรวจ Username / Password
*/
const loginAdmin = () => {
  router.push('/admin/dashboard')
}

const goBack = () => {
  router.push('/')
}
</script>


<template>
  <div class="admin-login-page">

    <!-- LEFT -->
    <div class="image-side">
      <div class="image-overlay"></div>
    </div>


    <!-- RIGHT -->
    <div class="login-side">

      <!-- Back -->
      <button
        class="back-btn"
        type="button"
        @click="goBack"
      >
        <Undo2 :size="26" />
      </button>


      <div class="login-container">

        <!-- Header -->
        <div class="admin-title">

          <div class="admin-icon">
            <GraduationCap :size="22" />
          </div>

          <div>
            <h1>{{ t.adminLogin.title }}</h1>
            <p>{{ t.adminLogin.subtitle }}</p>
          </div>

        </div>


        <!-- Form -->
        <form @submit.prevent="loginAdmin">

          <div class="form-group">

            <label>
              {{ t.adminLogin.usernameLabel }}
            </label>

            <div class="input-wrapper">

              <BriefcaseBusiness
                class="input-icon"
                :size="17"
              />

              <input
                v-model="username"
                type="text"
              />

            </div>

          </div>


          <div class="form-group">

            <label>{{ t.adminLogin.passwordLabel }}</label>

            <div class="input-wrapper">

              <LockKeyhole
                class="input-icon"
                :size="17"
              />

              <input
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
              />

              <button
                class="eye-btn"
                type="button"
                @click="showPassword = !showPassword"
              >

                <EyeOff
                  v-if="showPassword"
                  :size="17"
                />

                <Eye
                  v-else
                  :size="17"
                />

              </button>

            </div>

          </div>


          <div class="login-options">

            <label class="remember">

              <input
                v-model="rememberMe"
                type="checkbox"
              />

              <span>
                {{ t.adminLogin.rememberMe }}
              </span>

            </label>


            <a
              href="#"
              @click.prevent
            >
              {{ t.adminLogin.forgotPassword }}
            </a>

          </div>


          <!-- Login -->
          <button
            class="sign-in-btn"
            type="submit"
          >

            {{ t.adminLogin.signInButton }}

            <ArrowRight :size="20" />

          </button>


          <p class="support-text">

            {{ t.adminLogin.newToPortal }}

            <a
              href="#"
              @click.prevent
            >
              {{ t.adminLogin.contactSupport }}
            </a>

            {{ t.adminLogin.forAccess }}

          </p>

        </form>

      </div>

    </div>

  </div>
</template>


<style scoped>
* {
  box-sizing: border-box;
}

.admin-login-page {
  width: 100%;
  min-height: 100vh;

  display: flex;

  background: white;
}


/* =========================
   Image Side
========================= */

.image-side {
  width: 51%;
  min-height: 100vh;

  position: relative;

  /*
    ใส่รูปของคุณเองตรงนี้ภายหลัง
  */
  background-image:
    linear-gradient(
      rgba(0, 63, 111, 0.05),
      rgba(0, 63, 111, 0.08)
    ),
    url('/admin-building.jpg');

  background-position: center;
  background-size: cover;
  background-repeat: no-repeat;

  background-color: #16658e;
}


/* =========================
   Login Side
========================= */

.login-side {
  width: 49%;

  min-height: 100vh;

  display: flex;
  justify-content: center;
  align-items: center;

  position: relative;

  padding: 60px;
}

.login-container {
  width: 100%;
  max-width: 520px;
}


/* =========================
   Back button
========================= */

.back-btn {
  position: absolute;

  right: 38px;
  top: 34px;

  width: 48px;
  height: 48px;

  border: none;
  border-radius: 9px;

  background: #a60bd5;
  color: white;

  display: flex;
  align-items: center;
  justify-content: center;

  cursor: pointer;

  transition: 0.2s;
}

.back-btn:hover {
  background: #9005bb;
}


/* =========================
   Title
========================= */

.admin-title {
  display: flex;
  align-items: center;
  gap: 14px;

  margin-bottom: 100px;
}

.admin-icon {
  width: 43px;
  height: 43px;

  display: flex;
  align-items: center;
  justify-content: center;

  border-radius: 9px;

  background: #a60bd5;
  color: white;
}

.admin-title h1 {
  margin: 0;

  color: #071442;

  font-size: 25px;
  font-weight: 600;
}

.admin-title p {
  margin: 3px 0 0;

  color: #777b85;

  font-size: 13px;
}


/* =========================
   Form
========================= */

.form-group {
  margin-bottom: 24px;
}

.form-group label {
  display: block;

  margin-bottom: 9px;

  font-size: 13px;

  color: #374151;
}

.input-wrapper {
  position: relative;
}

.input-wrapper input {
  width: 100%;
  height: 52px;

  padding: 0 45px;

  /* พื้นหลังขาวอมเทา */
  background: #f8fafc !important;

  border: 1px solid #d8dee9;
  border-radius: 7px;

  outline: none;

  /* สีตัวหนังสือตอนพิมพ์ */
  color: #1f2937 !important;

  font-size: 15px;
  font-family: inherit;

  color-scheme: light;

  transition: 0.2s;
}

/* Placeholder */
.input-wrapper input::placeholder {
  color: #9aa5b5;
  opacity: 1;
}

/* ตอนคลิกช่องกรอก */
.input-wrapper input:focus {
  background: #ffffff !important;

  border-color: #a60bd5;

  box-shadow:
    0 0 0 3px rgba(166, 11, 213, 0.08);
}

/* ป้องกัน Chrome Autofill เปลี่ยนสีช่อง */
.input-wrapper input:-webkit-autofill,
.input-wrapper input:-webkit-autofill:hover,
.input-wrapper input:-webkit-autofill:focus {
  -webkit-text-fill-color: #1f2937 !important;
  -webkit-box-shadow:
    0 0 0 1000px #f8fafc inset !important;

  transition:
    background-color 9999s ease-in-out 0s;
}

.input-icon {
  position: absolute;

  left: 14px;
  top: 50%;

  transform: translateY(-50%);

  color: #8c929c;
}

.eye-btn {
  position: absolute;

  top: 50%;
  right: 14px;

  transform: translateY(-50%);

  border: none;
  background: none;

  color: #8c929c;

  cursor: pointer;
}


/* =========================
   Options
========================= */

.login-options {
  display: flex;
  align-items: center;
  justify-content: space-between;

  margin: 4px 0 32px;
}

.remember {
  display: flex;
  align-items: center;
  gap: 8px;

  font-size: 13px;

  cursor: pointer;
}

.remember input {
  width: 17px;
  height: 17px;
}

.login-options a {
  color: #071442;

  font-size: 13px;

  text-decoration: none;
}


/* =========================
   Login button
========================= */

.sign-in-btn {
  width: 100%;
  height: 58px;

  border: none;
  border-radius: 7px;

  background: #a60bd5;

  color: white;

  font-size: 21px;

  display: flex;
  justify-content: center;
  align-items: center;
  gap: 6px;

  cursor: pointer;

  box-shadow:
    0 10px 20px rgba(166, 11, 213, 0.15);

  transition: 0.2s;
}

.sign-in-btn:hover {
  background: #9005bb;
}


/* =========================
   Support
========================= */

.support-text {
  margin-top: 43px;

  text-align: center;

  font-size: 14px;

  color: #555;
}

.support-text a {
  color: #168243;

  text-decoration: none;
}


/* =========================
   Responsive
========================= */

@media (max-width: 900px) {

  .image-side {
    display: none;
  }

  .login-side {
    width: 100%;

    padding: 35px;
  }

  .admin-title {
    margin-bottom: 70px;
  }

}

@media (max-width: 500px) {

  .login-side {
    padding: 25px;
  }

  .back-btn {
    right: 20px;
    top: 20px;

    width: 42px;
    height: 42px;
  }

  .admin-title h1 {
    font-size: 22px;
  }

}
</style>