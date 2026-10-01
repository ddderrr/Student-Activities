<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  GraduationCap,
  BriefcaseBusiness,
  LockKeyhole,
  Mail,
  Eye,
  EyeOff,
  ArrowRight,
  TriangleAlert
} from 'lucide-vue-next'
import { useLanguage } from '../../composables/useLanguage'
import {
  loginStudentWithPassword,
  setStudentSession
} from '../../constants/currentStudent'

const { t } = useLanguage()

const router = useRouter()

const email = ref('')
const password = ref('')
const rememberMe = ref(false)
const showPassword = ref(false)
const loginError = ref('')
const loginSubmitting = ref(false)

/*
  MOCK LOGIN (dev): อีเมล + รหัสผ่านของบัญชีทดสอบใน backend/student_bypass.py
  (chem@test.com / cs@test.com / demo@test.com รหัสผ่าน 1234)
*/
const loginStudent = async () => {
  loginError.value = ''

  const value = email.value.trim()

  if (!value) {
    loginError.value = t.value.studentLogin.emailRequiredError
    return
  }

  if (!password.value) {
    loginError.value = t.value.studentLogin.passwordRequiredError
    return
  }

  loginSubmitting.value = true

  try {
    const student = await loginStudentWithPassword(value, password.value)
    setStudentSession(student)
    router.push('/student/activities')
  } catch (error) {
    if (error.status === 404) {
      loginError.value = t.value.studentLogin.emailNotFoundError
    } else if (error.status === 401) {
      loginError.value = t.value.studentLogin.wrongPasswordError
      password.value = ''
    } else {
      loginError.value = t.value.studentLogin.backendUnavailableError
    }
  } finally {
    loginSubmitting.value = false
  }
}

const goAdminLogin = () => {
  router.push('/admin/login')
}
</script>

<template>
  <div class="login-page">

    <div class="login-card">

      <!-- Header -->
      <div class="header">
        <div class="brand">
          <div class="brand-icon">
            <GraduationCap :size="22" />
          </div>

          <div>
            <h1>{{ t.studentLogin.universityName }}</h1>
            <p>{{ t.studentLogin.facultyName }}</p>
          </div>
        </div>

        <button
          class="admin-btn"
          type="button"
          @click="goAdminLogin"
        >
          <BriefcaseBusiness :size="15" />
          {{ t.studentLogin.adminLogin }}
        </button>
      </div>


      <!-- Login Form -->
      <form novalidate @submit.prevent="loginStudent">

        <div class="form-group">
          <label for="student-login-email">{{ t.studentLogin.emailLabel }}</label>

          <div class="input-wrapper">
            <Mail
              class="input-icon"
              :size="17"
            />

            <input
              id="student-login-email"
              v-model="email"
              type="email"
              name="email"
              autocomplete="username"
              :placeholder="t.studentLogin.emailPlaceholder"
              @input="loginError = ''"
            />
          </div>
        </div>


        <div class="form-group">
          <label for="student-login-password">{{ t.studentLogin.passwordLabel }}</label>

          <div class="input-wrapper">
            <LockKeyhole
              class="input-icon"
              :size="17"
            />

            <input
              id="student-login-password"
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              name="password"
              autocomplete="current-password"
              @input="loginError = ''"
            />

            <button
              class="eye-btn"
              type="button"
              :aria-label="showPassword ? t.studentLogin.hidePassword : t.studentLogin.showPassword"
              :title="showPassword ? t.studentLogin.hidePassword : t.studentLogin.showPassword"
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


        <!-- options -->
        <div class="login-options">

          <label class="remember">
            <input
              v-model="rememberMe"
              type="checkbox"
            />

            <span>{{ t.studentLogin.rememberMe }}</span>
          </label>

          <a
            href="#"
            @click.prevent
          >
            {{ t.studentLogin.forgotPassword }}
          </a>

        </div>


        <p v-if="loginError" class="error-text" role="alert">
          <TriangleAlert :size="16" />
          {{ loginError }}
        </p>


        <!-- Sign In -->
        <button
          class="sign-in-btn"
          type="submit"
          :disabled="loginSubmitting"
        >
          {{ t.studentLogin.signInButton }}
          <ArrowRight :size="19" />
        </button>


        <p class="support-text">
          {{ t.studentLogin.newToPortal }}
          <a href="#" @click.prevent>
            {{ t.studentLogin.contactItSupport }}
          </a>
          {{ t.studentLogin.forAccess }}
        </p>

      </form>

    </div>

  </div>
</template>

<style scoped>
* {
  box-sizing: border-box;
}

.login-page {
  width: 100%;
  min-height: 100vh;

  display: flex;
  justify-content: center;
  align-items: center;

  background: #ffffff;

  padding: 30px;
}

.login-card {
  width: 100%;
  max-width: 550px;
}


/* =========================
   Header
========================= */

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;

  margin-bottom: 120px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-icon {
  width: 40px;
  height: 40px;

  display: flex;
  align-items: center;
  justify-content: center;

  background: #a100d4;
  color: white;

  border-radius: 9px;
}

.brand h1 {
  margin: 0;

  font-size: 23px;
  font-weight: 600;

  color: #071442;
}

.brand p {
  margin: 3px 0 0;

  font-size: var(--fs-small);
  color: #7c7c86;
}


/* =========================
   Admin Button
========================= */

.admin-btn {
  height: 38px;

  padding: 0 14px;

  display: flex;
  align-items: center;
  gap: 7px;

  background: white;

  border: 1px solid #9ca3af;
  border-radius: 6px;

  color: #111827;

  cursor: pointer;

  transition: 0.2s;
}

.admin-btn:hover {
  background: #f5f5f5;
}


/* =========================
   Form
========================= */

.form-group {
  margin-bottom: 24px;
}

.form-group label {
  display: block;

  margin-bottom: 8px;

  color: #374151;

  font-size: var(--fs-body);
}

.input-wrapper {
  position: relative;
}

.input-wrapper input {
  width: 100%;
  height: 52px;

  padding: 0 45px;

  /* ทำช่องกรอกเป็นขาวอมเทา */
  background: #f8fafc !important;

  border: 1px solid #d8dee9;
  border-radius: 7px;

  outline: none;

  /* ตัวหนังสือที่พิมพ์ */
  color: #1f2937 !important;

  font-size: var(--fs-lead);
  font-family: inherit;

  transition: 0.2s;
}

/* ถ้ามี placeholder */
.input-wrapper input::placeholder {
  color: #9aa5b5;
  opacity: 1;
}

/* ตอนกดช่องกรอก */
.input-wrapper input:focus {
  background: #ffffff !important;
  border-color: #a100d4;

  box-shadow:
    0 0 0 3px rgba(161, 0, 212, 0.08);
}

/* ป้องกัน browser autofill ทำสีช่องเพี้ยน */
.input-wrapper input:-webkit-autofill,
.input-wrapper input:-webkit-autofill:hover,
.input-wrapper input:-webkit-autofill:focus {
  -webkit-text-fill-color: #1f2937;
  -webkit-box-shadow: 0 0 0 1000px #f8fafc inset;
  transition: background-color 9999s ease-in-out 0s;
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

  right: 13px;
  top: 50%;

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
  justify-content: space-between;
  align-items: center;

  margin: 3px 0 30px;
}

.remember {
  display: flex;
  align-items: center;
  gap: 8px;

  font-size: var(--fs-body);
  color: #374151;

  cursor: pointer;
}

.remember input {
  width: 16px;
  height: 16px;
}

.login-options a {
  font-size: var(--fs-body);

  color: #071442;

  text-decoration: none;
}


/* =========================
   Sign In
========================= */

.sign-in-btn {
  width: 100%;
  height: 55px;

  border: none;
  border-radius: 7px;

  background: #a60bd5;

  color: white;

  font-size: 21px;
  font-weight: 500;

  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;

  cursor: pointer;

  transition: 0.2s;

  box-shadow:
    0 8px 18px rgba(161, 0, 212, 0.15);
}

.sign-in-btn:hover {
  background: #9005bb;
}

.sign-in-btn:disabled {
  opacity: 0.7;
  cursor: wait;
}

.error-text {
  margin: -8px 0 18px;
  padding: 10px 12px;

  display: flex;
  align-items: center;
  gap: 8px;

  border-radius: 8px;
  background: #fdeaea;
  color: #b42318;
  font-size: var(--fs-body);
}

.error-text svg {
  flex-shrink: 0;
}


/* =========================
   Support
========================= */

.support-text {
  text-align: center;

  margin-top: 34px;

  font-size: var(--fs-body);

  color: #555;
}

.support-text a {
  color: #168243;

  text-decoration: none;
}


/* =========================
   Mobile
========================= */

@media (max-width: 600px) {
  .login-page {
    padding: 24px;
  }

  .header {
    margin-bottom: 70px;
  }

  .brand h1 {
    font-size: 19px;
  }

  .brand p {
    font-size: var(--fs-caption);
  }

  .admin-btn {
    padding: 0 10px;

    font-size: var(--fs-small);
  }
}
</style>