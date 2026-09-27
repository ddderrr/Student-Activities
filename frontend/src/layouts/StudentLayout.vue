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

  Search,

  Bell,

  Menu,

  UserRound,

  X

} from 'lucide-vue-next'

import { useRoute, useRouter } from 'vue-router'

import StudentSideBar

  from '../components/Student/StudentSideBar.vue'

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

   Search

===================================================== */

const searchText = ref('')

provide(

  'studentSearch',

  searchText

)

const clearSearch = () => {

  searchText.value = ''

}



/* =====================================================

   Current Student

   Mock ก่อนต่อ Backend

===================================================== */

const currentStudent = ref({

  id: '670510659',

  name: 'Tanakit Wanprasert',

  email: 'tanakit@example.com',

  faculty: 'Faculty of Science',

  major: 'Computer Science',

  /*

    ตอนมีรูปจริง ใส่ URL จาก Backend ตรงนี้ได้เลย

    เช่น:

    avatar: '/uploads/student/670510659.jpg'

  */

  avatar: ''

})



/* =====================================================

   Notifications

   ดึงจาก GET /api/student/me/notifications
   activityId ที่ได้มาคือ external_activity_id (ใช้เปิด My Submissions)

===================================================== */

const notifications = ref([])

const fetchNotifications = async () => {

  try {

    const response = await fetch(

      `${API_BASE}/api/student/me/notifications`,

      { headers: studentHeaders() }

    )

    if (!response.ok) {

      throw new Error(
        t.value.studentLayout.cannotLoadNotifications
      )

    }

    notifications.value =

      await response.json()

  } catch (error) {

    notifications.value = []

  }

}



const unreadCount = computed(() => {

  return notifications.value.filter(

    notification => !notification.read

  ).length

})



/* =====================================================

   Dropdown State

===================================================== */

const notificationOpen = ref(false)

const profileOpen = ref(false)

const notificationWrapper = ref(null)

const profileWrapper = ref(null)



const toggleNotifications = () => {

  notificationOpen.value =

    !notificationOpen.value

  /*

    เปิด Notification แล้วปิด Profile

  */

  profileOpen.value = false

}



const toggleProfile = () => {

  profileOpen.value =

    !profileOpen.value

  /*

    เปิด Profile แล้วปิด Notification

  */

  notificationOpen.value = false

}



/* =====================================================

   Notification Actions

===================================================== */

const openNotification = async (notification) => {

  /*

    ถือว่าอ่านข้อความนี้แล้ว (อัปเดตทั้งฝั่ง UI และ backend)

  */

  notification.read = true

  notificationOpen.value = false

  profileOpen.value = false

  fetch(

    `${API_BASE}/api/student/me/notifications/${notification.id}/read`,

    { method: 'PATCH', headers: studentHeaders() }

  ).catch(() => {})

  /*

    ส่ง activityId ไปให้ StudentActivities.vue

    ตัวอย่าง:

    /student/activities?open=4

    StudentActivities.vue จะเปิด Modal

    ของ Activity id 4 ให้อัตโนมัติ

  */

  if (!notification.activityId) return

  await router.push({

    path: '/student/activities',

    query: {

      open: notification.activityId

    }

  })

}



const markAllAsRead = () => {

  notifications.value.forEach(

    notification => {

      notification.read = true

    }

  )

  fetch(

    `${API_BASE}/api/student/me/notifications/mark-all-read`,

    { method: 'PATCH', headers: studentHeaders() }

  ).catch(() => {})

}



/* =====================================================

   Click Outside

   กดพื้นที่ว่างแล้วปิด Notification / Profile

===================================================== */

const closeDropdownOnOutside = (event) => {

  /*

    Notification

  */

  if (

    notificationOpen.value &&

    notificationWrapper.value &&

    !notificationWrapper.value.contains(event.target)

  ) {

    notificationOpen.value = false

  }



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

  fetchNotifications()

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

        <!-- Search -->

        <div class="search-box">

          <Search :size="17" />

          <input

            v-model="searchText"

            type="text"

            :placeholder="t.studentLayout.searchPlaceholder"

          />

          <button

            v-if="searchText"

            class="clear-search"

            type="button"

            :aria-label="t.studentLayout.clearSearch"

            @click="clearSearch"

          >

            <X :size="15" />

          </button>

        </div>



        <!-- =================================================

             Right Actions

        ================================================== -->

        <div class="top-actions">

          <!-- =========================

               Notification

          ========================== -->

          <div

            ref="notificationWrapper"

            class="action-wrapper"

          >

            <button

              class="icon-button notification-button"

              type="button"

              :title="t.studentLayout.notifications"

              :aria-label="t.studentLayout.notifications"

              @click.stop="toggleNotifications"

            >

              <Bell :size="19" />

              <!-- จุดแดง -->

              <span

                v-if="unreadCount > 0"

                class="notification-dot"

              ></span>

            </button>



            <!-- Notification Dropdown -->

            <div

              v-if="notificationOpen"

              class="dropdown notification-dropdown"

              @click.stop

            >

              <div class="dropdown-header">

                <div>

                  <strong>

                    {{ t.studentLayout.notifications }}

                  </strong>

                  <span>

                    {{ unreadCount }} {{ t.studentLayout.unread }}

                  </span>

                </div>



                <button

                  v-if="unreadCount > 0"

                  type="button"

                  @click="markAllAsRead"

                >

                  {{ t.studentLayout.markAllRead }}

                </button>

              </div>



              <div

                v-if="notifications.length > 0"

                class="notification-list"

              >

                <button

                  v-for="notification in notifications"

                  :key="notification.id"

                  class="notification-item"

                  :class="{

                    unread: !notification.read

                  }"

                  type="button"

                  @click="openNotification(notification)"

                >

                  <div

                    class="notification-status"

                    :class="

                      notification.status.toLowerCase()

                    "

                  ></div>



                  <div class="notification-text">

                    <strong>

                      {{ notification.title }}

                    </strong>

                    <p>

                      {{ notification.message }}

                    </p>

                  </div>

                </button>

              </div>



              <div

                v-else

                class="dropdown-empty"

              >

                {{ t.studentLayout.noNotifications }}

              </div>

            </div>

          </div>



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

  justify-content: space-between;

  padding: 0 28px;

  background: white;

  border-bottom: 1px solid #eceef3;

  box-sizing: border-box;

}



/* =====================================================

   Search

===================================================== */

.search-box {

  width: 420px;

  max-width: 50%;

  height: 38px;

  display: flex;

  align-items: center;

  gap: 9px;

  padding: 0 14px;

  background: #f8f9fb;

  border: 1px solid #e0e3e8;

  border-radius: 20px;

  color: #9ca3af;

  box-sizing: border-box;

}



.search-box:focus-within {

  border-color: #b5c0ff;

  background: white;

  box-shadow:

    0 0 0 3px rgba(67, 89, 255, 0.07);

}



.search-box input {

  flex: 1;

  min-width: 0;

  border: none;

  outline: none;

  background: transparent;

  font-size: 13px;

  /* ตัวที่พิมพ์ให้เป็นสีเข้ม */

  color: #303846;

}



/* placeholder ให้เห็นชัด */

.search-box input::placeholder {

  color: #9ca3af;

  opacity: 1;

}



.clear-search {

  display: flex;

  align-items: center;

  justify-content: center;

  padding: 0;

  border: none;

  background: transparent;

  color: #8d96a5;

  cursor: pointer;

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

   Notification Dot

===================================================== */

.notification-dot {

  position: absolute;

  top: 4px;

  right: 5px;

  width: 8px;

  height: 8px;

  border: 2px solid white;

  border-radius: 50%;

  background: #ef4444;

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

   Notifications

===================================================== */

.notification-dropdown {

  width: 340px;

  overflow: hidden;

}



.dropdown-header {

  display: flex;

  justify-content: space-between;

  align-items: center;

  padding: 15px;

  border-bottom: 1px solid #edf0f4;

}



.dropdown-header div {

  display: flex;

  flex-direction: column;

  gap: 3px;

}



.dropdown-header strong {

  color: #253047;

  font-size: 14px;

}



.dropdown-header span {

  color: #929baa;

  font-size: 10px;

}



.dropdown-header button {

  border: none;

  background: transparent;

  color: #345eea;

  font-size: 10px;

  cursor: pointer;

}



.notification-list {

  max-height: 320px;

  overflow-y: auto;

}



.notification-item {

  width: 100%;

  display: flex;

  gap: 11px;

  padding: 14px;

  border: none;

  border-bottom: 1px solid #f0f2f5;

  background: white;

  text-align: left;

  cursor: pointer;

}



.notification-item:hover {

  background: #f8f9fc;

}



.notification-item.unread {

  background: #f5f7ff;

}



.notification-status {

  width: 8px;

  height: 8px;

  flex-shrink: 0;

  margin-top: 5px;

  border-radius: 50%;

}



.notification-status.pending {

  background: #f5a623;

}



.notification-status.rejected {

  background: #e64b4b;

}



.notification-status.approved {

  background: #20bd68;

}



.notification-text {

  min-width: 0;

}



.notification-text strong {

  display: block;

  color: #2c3442;

  font-size: 11px;

}



.notification-text p {

  margin: 5px 0 0;

  color: #7f8998;

  font-size: 10px;

  line-height: 1.45;

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

  font-size: 14px;

}



.profile-id {

  display: block;

  margin-top: 3px;

  color: #929baa;

  font-size: 10px;

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

  font-size: 9px;

}



.profile-info strong {

  color: #3c4555;

  font-size: 11px;

  font-weight: 600;

  overflow-wrap: anywhere;

}



.dropdown-empty {

  padding: 25px;

  text-align: center;

  color: #929baa;

  font-size: 11px;

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



  .search-box {

    width: 300px;

    max-width: 55%;

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



  .search-box {

    width: 100%;

    max-width: none;

    flex: 1;

  }



  .top-actions {

    flex-shrink: 0;

    gap: 7px;

  }



  .notification-dropdown {

    width:

      min(

        340px,

        calc(100vw - 30px)

      );

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



  .search-box input {

    font-size: 11px;

  }

}

</style>