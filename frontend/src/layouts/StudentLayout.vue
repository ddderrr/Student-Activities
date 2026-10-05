<script setup>

import {

  ref,

  provide,

  computed,

  onMounted,

  onBeforeUnmount,

  watch

} from 'vue'

import {

  LogOut,

  Menu,

  UserRound

} from 'lucide-vue-next'

import { useRoute, useRouter } from 'vue-router'

import StudentNotificationBell

  from '../components/Student/StudentNotificationBell.vue'

import StudentSideBar

  from '../components/Student/StudentSideBar.vue'

import { logout as logoutAll } from '../constants/auth'
import { API_BASE, studentHeaders } from '../constants/currentStudent'
import { useLanguage } from '../composables/useLanguage'

const router = useRouter()

const route = useRoute()

const { t } = useLanguage()



/* =====================================================

   Sidebar

   จอ ≤700px (breakpoint เดียวกับ CSS) sidebar เป็น drawer ทับหน้า

   จึงเริ่มแบบปิด ส่วนจอใหญ่เริ่มแบบกางเหมือนเดิม

===================================================== */

const mobileQuery = window.matchMedia('(max-width: 700px)')

const sidebarOpen = ref(!mobileQuery.matches)

const toggleSidebar = () => {

  sidebarOpen.value = !sidebarOpen.value

}

// ย่อ/ขยายจอข้าม breakpoint: เข้ามือถือ = ปิด drawer, กลับจอใหญ่ = กาง

const onMobileQueryChange = (event) => {

  sidebarOpen.value = !event.matches

}

// มือถือ: เปลี่ยนหน้าแล้วปิด drawer ไม่ให้บังหน้าใหม่

watch(

  () => route.fullPath,

  () => {

    if (mobileQuery.matches) sidebarOpen.value = false

  }

)

const closeSidebarOnEscape = (event) => {

  if (event.key === 'Escape' && mobileQuery.matches && sidebarOpen.value) {

    sidebarOpen.value = false

  }

}

provide(

  'toggleStudentSidebar',

  toggleSidebar

)



/* =====================================================

   Current Student

   ดึงจาก GET /api/student/me เสมอ (ไม่ hardcode ตายตัว) เพื่อให้ profile ที่
   โชว์ตรงกับ identity จริงที่ studentHeaders() ส่งไปทุก endpoint -- ก่อนหน้านี้
   ค่านี้ hardcode เป็น 670510659 ไว้ตลอด ทำให้ดูเหมือน login เป็นคนเดิมแม้จะ
   สลับ mock student คนอื่นจากหน้า login แล้วก็ตาม

===================================================== */

const currentStudent = ref({

  id: '',

  name: '',

  email: '',

  faculty: '',

  major: '',

  avatar: ''

})

const fetchCurrentStudent = async () => {

  try {

    const response = await fetch(

      `${API_BASE}/api/student/me`,

      { headers: studentHeaders() }

    )

    if (!response.ok) {

      throw new Error(
        t.value.studentLayout.cannotLoadNotifications
      )

    }

    const student = await response.json()

    currentStudent.value = {

      id: student.student_id,

      name: student.name,

      email: student.email,

      faculty: student.faculty,

      major: student.major || '',

      avatar: ''

    }

  } catch (error) {

    // เงียบไว้: header/profile ยังใช้งานหน้าอื่นต่อได้ แค่ไม่โชว์ชื่อ/สาขา

  }

}

const logoutStudent = () => {

  profileOpen.value = false
  logoutAll()
  router.push('/login')

}



/* =====================================================

   Dropdown State

===================================================== */

const profileOpen = ref(false)

const profileWrapper = ref(null)

const toggleProfile = () => {

  profileOpen.value = !profileOpen.value

}



/* =====================================================

   Click Outside

   กดพื้นที่ว่างแล้วปิด Notification / Profile

===================================================== */

const closeDropdownOnOutside = (event) => {

  /*

    Profile

  */

  if (

    profileOpen.value &&

    profileWrapper.value &&

    !profileWrapper.value.contains(event.target)

  ) {

    profileOpen.value = false

  }

}



onMounted(() => {

  document.addEventListener(

    'click',

    closeDropdownOnOutside

  )

  document.addEventListener(

    'keydown',

    closeSidebarOnEscape

  )

  mobileQuery.addEventListener(

    'change',

    onMobileQueryChange

  )

  fetchCurrentStudent()

})



onBeforeUnmount(() => {

  document.removeEventListener(

    'click',

    closeDropdownOnOutside

  )

  document.removeEventListener(

    'keydown',

    closeSidebarOnEscape

  )

  mobileQuery.removeEventListener(

    'change',

    onMobileQueryChange

  )

})

</script>



<template>

  <div class="student-layout" :class="{ 'sidebar-open': sidebarOpen }">

    <!-- =================================================

         Sidebar

    ================================================== -->

    <StudentSideBar
      class="sidebar-component"
      :collapsed="!sidebarOpen"
      @toggle="toggleSidebar"
    />



    <!-- =================================================

         Main

    ================================================== -->

    <main class="main">

      <!-- =================================================

           Topbar

      ================================================== -->

      <header class="topbar">



        <!-- =================================================

             Right Actions

        ================================================== -->

        <div class="top-actions">

          <!-- =========================

               Notification (StudentNotificationBell.vue)

          ========================== -->

          <StudentNotificationBell />



          <!-- =========================

               Sidebar Toggle

          ========================== -->

          <button

            class="icon-button"

            type="button"

            :title="t.studentLayout.toggleSidebar"

            :aria-label="t.studentLayout.toggleSidebar"

            @click="toggleSidebar"

          >

            <Menu :size="21" />

          </button>



          <!-- =========================

               Profile

          ========================== -->

          <div

            ref="profileWrapper"

            class="action-wrapper"

          >

            <button

              class="profile"

              type="button"

              :title="t.studentLayout.myProfile"

              :aria-label="t.studentLayout.myProfile"

              @click.stop="toggleProfile"

            >

              <img

                v-if="currentStudent.avatar"

                :src="currentStudent.avatar"

                :alt="t.studentLayout.studentProfileAlt"

              />

              <UserRound

                v-else

                :size="19"

              />

            </button>



            <!-- Profile Dropdown -->

            <div

              v-if="profileOpen"

              class="dropdown profile-dropdown"

              @click.stop

            >

              <div class="profile-avatar">

                <img

                  v-if="currentStudent.avatar"

                  :src="currentStudent.avatar"

                  :alt="t.studentLayout.studentProfileAlt"

                />

                <UserRound

                  v-else

                  :size="30"

                />

              </div>



              <strong class="profile-name">

                {{ currentStudent.name }}

              </strong>

              <span class="profile-id">

                {{ t.studentLayout.idLabel }}: {{ currentStudent.id }}

              </span>



              <div class="profile-info">

                <div>

                  <span>{{ t.studentLayout.faculty }}</span>

                  <strong>

                    {{ currentStudent.faculty }}

                  </strong>

                </div>



                <div>

                  <span>{{ t.studentLayout.major }}</span>

                  <strong>

                    {{ currentStudent.major }}

                  </strong>

                </div>



                <div>

                  <span>{{ t.studentLayout.email }}</span>

                  <strong>

                    {{ currentStudent.email }}

                  </strong>

                </div>

              </div>



              <button
                class="logout-button"
                type="button"
                @click="logoutStudent"
              >

                <LogOut :size="16" />

                {{ t.studentLayout.logoutAndSwitchStudent }}

              </button>

            </div>

          </div>

        </div>

      </header>



      <!-- =================================================

           Page

      ================================================== -->

      <section class="page-content">

        <RouterView />

      </section>

    </main>



    <!-- =================================================

         Mobile Overlay

    ================================================== -->

    <div

      v-if="sidebarOpen"

      class="mobile-overlay"

      @click="sidebarOpen = false"

    ></div>

  </div>

</template>



<style scoped>

/* =====================================================

   Layout

===================================================== */

.student-layout {

  min-height: 100vh;

  display: flex;

  background: #f5f7fb;

  /* clip แทน hidden: hidden ทำให้ layout เป็น scroll container แล้ว sidebar sticky ไม่ทำงาน */
  overflow-x: clip;

}



/* =====================================================

   Sidebar

===================================================== */

.sidebar-component {

  flex-shrink: 0;

  transition:

    width 0.25s ease,

    padding 0.25s ease,

    opacity 0.2s ease,

    transform 0.25s ease;

}






/* =====================================================

   Main

===================================================== */

.main {

  flex: 1;

  min-width: 0;

  min-height: 100vh;

}



/* =====================================================

   Topbar

===================================================== */

.topbar {

  position: relative;

  z-index: 100;

  height: 64px;

  display: flex;

  align-items: center;

  justify-content: flex-end;

  padding: 0 28px;

  background: white;

  border-bottom: 1px solid #eceef3;

  box-sizing: border-box;

}



/* =====================================================

   Actions

===================================================== */

.top-actions {

  display: flex;

  align-items: center;

  gap: 18px;

  color: #75869c;

}



.action-wrapper {

  position: relative;

}



.icon-button {

  position: relative;

  width: 34px;

  height: 34px;

  display: flex;

  align-items: center;

  justify-content: center;

  border: none;

  border-radius: 8px;

  background: transparent;

  color: inherit;

  cursor: pointer;

  transition:

    background 0.15s ease,

    color 0.15s ease;

}



.icon-button:hover {

  color: #345eea;

  background: #f1f4ff;

}



/* =====================================================

   Profile Button

===================================================== */

.profile {

  width: 36px;

  height: 36px;

  display: flex;

  align-items: center;

  justify-content: center;

  padding: 0;

  overflow: hidden;

  border: none;

  border-radius: 50%;

  background: #f1f4f8;

  color: #75869c;

  cursor: pointer;

}



.profile:hover {

  background: #e8ecf4;

}



.profile img {

  width: 100%;

  height: 100%;

  object-fit: cover;

}



/* =====================================================

   Dropdown

===================================================== */

.dropdown {

  position: absolute;

  top: 46px;

  right: 0;

  z-index: 500;

  background: white;

  border: 1px solid #e4e8ef;

  border-radius: 12px;

  box-shadow:

    0 12px 35px rgba(30, 40, 70, 0.16);

}



/* =====================================================

   Profile Dropdown

===================================================== */

.profile-dropdown {

  width: 280px;

  padding: 20px;

  text-align: center;

}



.profile-avatar {

  width: 64px;

  height: 64px;

  display: flex;

  align-items: center;

  justify-content: center;

  margin: 0 auto 10px;

  overflow: hidden;

  border-radius: 50%;

  background: #eef1f7;

  color: #657389;

}



.profile-avatar img {

  width: 100%;

  height: 100%;

  object-fit: cover;

}



.profile-name {

  display: block;

  color: #263044;

  font-size: var(--fs-body);

}



.profile-id {

  display: block;

  margin-top: 3px;

  color: #929baa;

  font-size: var(--fs-caption);

}



.profile-info {

  display: flex;

  flex-direction: column;

  gap: 12px;

  margin-top: 18px;

  padding-top: 15px;

  border-top: 1px solid #edf0f4;

  text-align: left;

}



.profile-info div {

  display: flex;

  flex-direction: column;

  gap: 3px;

}



.profile-info span {

  color: #949dab;

  font-size: var(--fs-badge);

}



.profile-info strong {

  color: #3c4555;

  font-size: var(--fs-small);

  font-weight: 600;

  overflow-wrap: anywhere;

}



.logout-button {

  width: 100%;

  margin-top: 14px;
  padding: 9px 10px;

  display: flex;
  align-items: center;
  gap: 8px;
  justify-content: center;

  border: 1px solid #f0d5d5;
  border-radius: 8px;

  background: #fdf5f5;
  color: #b42318;

  font: inherit;
  font-size: var(--fs-small);
  font-weight: 600;

  cursor: pointer;
  transition: 0.2s;

}

.logout-button:hover {

  background: #fbe9e9;

}



/* =====================================================

   Content

===================================================== */

.page-content {

  min-width: 0;

}



/* =====================================================

   Mobile Overlay

===================================================== */

.mobile-overlay {

  display: none;

}



/* =====================================================

   Tablet

===================================================== */

@media (max-width: 900px) {

  .topbar {

    padding: 0 20px;

  }

}



/* =====================================================

   Mobile

===================================================== */

@media (max-width: 700px) {

  .sidebar-component {
    position: fixed;
    top: 0;
    left: 0;
    z-index: 1001;
    height: 100vh;
    transform: translateX(-100%);
    transition: transform 0.25s ease;
  }

  .student-layout.sidebar-open .sidebar-component {
    transform: translateX(0);
  }



  .mobile-overlay {

    position: fixed;

    inset: 0;

    z-index: 1000;

    display: block;

    background:

      rgba(15, 23, 42, 0.25);

  }



  .topbar {

    padding: 0 14px;

    gap: 12px;

  }



  .top-actions {

    flex-shrink: 0;

    gap: 7px;

  }



  .profile-dropdown {

    width:

      min(

        280px,

        calc(100vw - 30px)

      );

  }

}



/* =====================================================

   Small Mobile

===================================================== */

@media (max-width: 480px) {

  .profile {

    width: 32px;

    height: 32px;

  }

}

</style>