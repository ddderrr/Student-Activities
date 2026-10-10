export default {
  skillMetrics: {
    exposureShort: 'ประสบการณ์ทักษะ',
    level: 'ระดับทักษะ',
    exposure: 'ชั่วโมงประสบการณ์ทักษะ',
    activities: 'กิจกรรม',
    noData: 'ไม่มีข้อมูลทักษะ',
    externalNoComparison: 'กิจกรรมภายนอกไม่มีการเปรียบเทียบค่าเฉลี่ย'
  },
  skillSources: {
    major: "กิจกรรมสาขา",
    faculty: "กิจกรรมคณะ",
    external: "กิจกรรมภายนอก",
    externalTitle: "ทักษะจากกิจกรรมภายนอก",
    externalHint: "ทักษะจากกิจกรรมภายนอกที่ได้รับการอนุมัติของนักศึกษาคนนี้เท่านั้น",
    externalEmpty: "ยังไม่มีข้อมูลทักษะจากกิจกรรมภายนอกที่ได้รับการอนุมัติ",
    strongestExternal: "ทักษะภายนอกที่โดดเด่นที่สุด",
    internalActivities: "กิจกรรมภายในมหาวิทยาลัย",
    activitiesUsed: "กิจกรรมที่ใช้คำนวณ",
    sourceLabel: "แหล่งกิจกรรม",
    sourceCaption: "แหล่งข้อมูล",
    personalSource: "กิจกรรมภายนอกที่ได้รับการอนุมัติ"
  },
  activityHours: {
    major: 'ชั่วโมงกิจกรรมของสาขา',
    faculty: 'ชั่วโมงกิจกรรมของคณะ',
    external: 'ชั่วโมงกิจกรรมภายนอก',

    label: 'ชั่วโมงกิจกรรม',
    total: 'ชั่วโมงกิจกรรมสะสมทั้งหมด',
    unit: 'ชั่วโมง',
    invalid: 'กรอกชั่วโมงมากกว่า 0 และทศนิยมไม่เกิน 2 ตำแหน่ง',
    invalidEdit: 'กรอกชั่วโมงตั้งแต่ 0 และทศนิยมไม่เกิน 2 ตำแหน่ง'
  },
  common: {
    language: 'ภาษา',
    thai: 'ไทย',
    english: 'อังกฤษ',
    helpCenter: 'ศูนย์ช่วยเหลือ',
    helpCenterContact: 'ติดต่อทางอีเมล',
    logout: 'ออกจากระบบ',
    settings: 'ตั้งค่า',
    branchLabel: 'สาขา',
    allBranches: 'ทุกสาขา'
  },

  adminSidebar: {
    faculty: 'คณะวิทยาศาสตร์',
    subtitle: 'ระบบจัดการสำหรับผู้ดูแล',

    dashboard: 'แดชบอร์ด',
    activities: 'กิจกรรม',
    studentSkills: 'ทักษะนักศึกษา',
    approvals: 'การอนุมัติ',

    centralAdmin: 'แอดมินกลาง · ทุกสาขา',
    majorPrefix: 'สาขา',

    userGuide: 'คู่มือการใช้งาน',
    openSidebar: 'เปิดแถบเมนู',
    closeSidebar: 'ปิดแถบเมนู'
  },

  studentSidebar: {
    faculty: 'คณะวิทยาศาสตร์',
    subtitle: 'ระบบติดตามความก้าวหน้าของนักศึกษา',

    myActivities: 'กิจกรรมของฉัน',
    mySkills: 'ทักษะของฉัน',
    addExternalActivity: 'เพิ่มกิจกรรมภายนอก',
    transcript: 'ทรานสคริปต์กิจกรรม',

    userGuide: 'คู่มือการใช้งาน',
    openSidebar: 'เปิดแถบเมนู',
    closeSidebar: 'ปิดแถบเมนู'
  },

  studentCalendar: {
    title: 'ปฏิทินกิจกรรม',
    description: 'กิจกรรมที่คณะและสาขาของคุณจัด ดูล่วงหน้าเพื่อเตรียมตัว กดที่กิจกรรมเพื่อดูรายละเอียด',
    sourceLabel: 'จัดโดย',
    locationLabel: 'สถานที่',
    hoursLabel: 'ชั่วโมงกิจกรรม',
    joinLabel: 'การเข้าร่วม',
    joinedAsParticipant: 'เข้าร่วมแล้ว (ผู้เข้าร่วม)',
    joinedAsOrganizer: 'เข้าร่วมแล้ว (ผู้จัด)',
    notJoined: 'ยังไม่ได้เข้าร่วม',
    sources: {
      faculty: 'คณะ (กิจกรรมส่วนกลาง)',
      major: 'สาขาของคุณ',
      external: 'กิจกรรมภายนอก'
    }
  },

  activityCalendar: {
    title: 'ปฏิทินกิจกรรม',
    description: 'กิจกรรมทั้งหมดทั้งที่ผ่านมาแล้วและที่กำลังจะมาถึง กดที่กิจกรรมเพื่อดูรายละเอียด',
    previousMonth: 'เดือนก่อนหน้า',
    nextMonth: 'เดือนถัดไป',
    today: 'วันนี้',
    legendUpcoming: 'กำลังจะมาถึง / กำลังดำเนินการ',
    legendPast: 'ผ่านมาแล้ว',
    legendCancelled: 'ยกเลิกแล้ว',
    more: '+{count} เพิ่มเติม',
    empty: 'ไม่มีกิจกรรมในเดือนนี้',
    loadError: 'โหลดกิจกรรมไม่สำเร็จ',
    close: 'ปิด',
    dateLabel: 'วันที่',
    organizerLabel: 'ผู้จัด',
    participantsLabel: 'ผู้เข้าร่วม',
    participantsCount: '{count} คน',
    branchLabel: 'สาขา',
    facultyWide: 'กิจกรรมส่วนกลางของคณะ',
    viewDetails: 'ดูรายละเอียดกิจกรรม →',
    statusUpcoming: 'กำลังจะมาถึง',
    statusOngoing: 'กำลังดำเนินการ',
    statusPast: 'ผ่านมาแล้ว',
    statusCancelled: 'ยกเลิกแล้ว',
    typeLabel: 'ประเภท',
    scopeLabel: 'แสดงกิจกรรม',
    scopeAll: 'ทุกกิจกรรม',
    scopeMine: 'เฉพาะสาขา{major}',
    types: {
      academic: 'กิจกรรมวิชาการ',
      seminar: 'สัมมนา',
      training: 'อบรม / Workshop',
      volunteer: 'จิตอาสา',
      skill: 'กิจกรรมพัฒนาทักษะ',
      recreation: 'กิจกรรมนันทนาการ',
      other: 'อื่นๆ'
    }
  },

  adminDashboard: {
  title: 'แดชบอร์ด',
  subtitle: 'ภาพรวมกิจกรรมของคณะและการเข้าร่วมของนักศึกษา',

  activities: 'กิจกรรม',
  students: 'นักศึกษา',
  participants: 'ผู้เข้าร่วม',
  completionRate: 'อัตราการสำเร็จ',

  activityGrowth: 'การเติบโตของกิจกรรม',
  activityGrowthDescription: 'จำนวนกิจกรรมที่สร้างขึ้นในแต่ละช่วงเวลา',

  monthly: 'รายเดือน',
  quarterly: 'รายไตรมาส',

  skillDistribution: 'การกระจายทักษะของนักศึกษา',
  skillDescription: 'ระดับความสามารถเฉลี่ยในทักษะหลัก',

  criticalThinking: 'การคิดเชิงวิพากษ์',
  communication: 'การสื่อสาร',
  leadership: 'ภาวะผู้นำ',

  averageScore: 'คะแนนเฉลี่ย',

  systemStatus: 'สถานะระบบ',
  loadingData: 'กำลังโหลดข้อมูล',
  waitingBackend: 'กำลังรอ Backend',
  ready: 'พร้อมใช้งาน',

  dashboardHistory: 'ประวัติแดชบอร์ด',
  dashboardHistoryDescription: 'เลือกปีและภาคเรียนเพื่อดู Summary, Activity Growth และ Skill Distribution ย้อนหลัง',
  academicYear: 'ปีการศึกษา',
  semester: 'ภาคเรียน',
  allSemesters: 'ทุกภาคเรียน',
  semester1: 'ภาคเรียนที่ 1',
  semester2: 'ภาคเรียนที่ 2',
  participantRole: 'ผู้เข้าร่วม',
  staffRole: 'บุคลากร',
  activitiesUnit: 'กิจกรรม',
  noData: 'ไม่มีข้อมูล',
  monthJan: 'ม.ค.',
  monthFeb: 'ก.พ.',
  monthMar: 'มี.ค.',
  monthApr: 'เม.ย.',
  monthMay: 'พ.ค.',
  monthJun: 'มิ.ย.',
  monthJul: 'ก.ค.',
  monthAug: 'ส.ค.',
  monthSep: 'ก.ย.',
  monthOct: 'ต.ค.',
  monthNov: 'พ.ย.',
  monthDec: 'ธ.ค.',
  quarterQ1: 'ไตรมาส 1',
  quarterQ2: 'ไตรมาส 2',
  quarterQ3: 'ไตรมาส 3',
  quarterQ4: 'ไตรมาส 4'
 },

 adminStudentSkills: {
  title: 'ทักษะนักศึกษา',
  subtitle: 'ภาพรวมระดับทักษะของนักศึกษาภายในคณะ',

  averageSkillScore: 'คะแนนทักษะเฉลี่ย',
  thisSemester: '— ภาคการศึกษานี้',
  studentsEvaluated: 'นักศึกษาที่ประเมินแล้ว',
  ofTotalFaculty: 'ของนักศึกษาทั้งคณะ',

  facultyRadar: 'เรดาร์ทักษะภาพรวมของคณะ',
  actualProficiency: 'ระดับทักษะจริง',
  benchmarkLevel: 'ระดับมาตรฐาน',

  leadership: 'ภาวะผู้นำ',
  criticalThinking: 'การคิดเชิงวิพากษ์',
  communication: 'การสื่อสาร',
  teamwork: 'การทำงานเป็นทีม',
  creativity: 'ความคิดสร้างสรรค์',
  digitalLiteracy: 'ความรู้ดิจิทัล',

  topArea: 'ทักษะเด่น',
  facultyAverage: 'ค่าเฉลี่ยของคณะ',
  highestScore: 'คะแนนทักษะสูงสุด',

  growthArea: 'ทักษะที่ควรพัฒนา',
  actionPlan: 'แนวทางพัฒนา',

  individualSkills: 'ทักษะรายบุคคล',
  searchPlaceholder: 'รหัสหรือชื่อนักศึกษา...',
  filterStudents: 'กรองนักศึกษา',
  primarySkill: 'ทักษะเด่น',
  scoreAverage: 'คะแนนเฉลี่ย',

  allSkills: 'ทุกทักษะ',
  allScores: 'ทุกช่วงคะแนน',

  studentName: 'ชื่อนักศึกษา',
  studentId: 'รหัสนักศึกษา',
  scoreAvg: 'คะแนนเฉลี่ย',
  action: 'การดำเนินการ',
  viewRadar: 'ดูเรดาร์',
  viewActivities: 'ดูกิจกรรม',
  noStudentData: 'ไม่มีข้อมูลทักษะนักศึกษา',

  major: 'สาขาวิชา',

  cohortFilterTitle: 'แสดง Skill ของ',
  yearLevelFilterLabel: 'ชั้นปี',
  allYearLevels: 'ทุกชั้นปี',
  yearLevel1: 'ปี 1',
  yearLevel2: 'ปี 2',
  yearLevel3: 'ปี 3',
  yearLevel4: 'ปี 4',
  yearLevel5Plus: 'ปี 5 ขึ้นไป',
  yearLevelUnknown: 'ไม่ทราบชั้นปี',
  yearLevelColumn: 'ชั้นปี',
  yearLevelHint: 'ชั้นปีคิดจากปีที่เข้าศึกษาในรหัสนักศึกษา (2 หลักแรก) และขึ้นชั้นปีใหม่ทุกเดือนกรกฎาคม',
  groupAverage: 'ค่าเฉลี่ยของกลุ่ม',

  radarViewLabel: 'มุมมอง',
  radarViewOverall: 'ภาพรวม',
  radarViewByYear: 'แยกชั้นปี',
  radarViewByMajor: 'แยกสาขา',
  radarViewByMajorYear: 'แยกสาขา × ชั้นปี',
  radarGroupHint: 'เลือกได้สูงสุด 3 กลุ่มเพื่อแสดงบน radar',
  avgShort: 'เฉลี่ย',
  showGroupTable: 'ดูตัวเลขของแต่ละกลุ่ม',
  groupColumn: 'กลุ่ม',
  studentsColumn: 'นักศึกษา',
  skillShortArtsCultureTraditions: 'ศิลปวัฒนธรรม',
  skillShortVolunteerism: 'จิตอาสา',
  skillShortAcademics: 'วิชาการ',
  skillShortInternationalization: 'นานาชาติ',
  skillShortHealthPromotion: 'สุขภาพ',
  skillShortNatureEnvironmentalConservation: 'สิ่งแวดล้อม',
  skillShortCreativeLeadership: 'ภาวะผู้นำ',
  skillShortInnovation: 'นวัตกรรม',
  skillShortEntrepreneurship: 'ผู้ประกอบการ',
  skillShortPromoteEquality: 'ความเท่าเทียม',
  skillShortAcademic: 'วิชาการ',
  skillShortNatureEnvironmental: 'สิ่งแวดล้อม',
  skillTrackLabel: 'ชุด Skill',
  skillTrackParticipant: 'Skill ผู้เข้าร่วม',
  skillTrackStaff: 'Skill ผู้จัด (Staff)',
  skillTrackStaffHint: 'Skill ผู้จัดมาจากกิจกรรมที่นักศึกษาเป็นผู้จัด (organizer)',
  majorFilterLabel: 'สาขาวิชา',
  allMajors: 'ทุกสาขา',
  majorNotSpecified: 'ไม่ระบุสาขา',
  clearCohortFilters: 'ล้างตัวกรอง',
  ofSelectedGroup: 'ของนักศึกษาในกลุ่มนี้',

  skillAnalysis: 'การวิเคราะห์ระดับทักษะ',
  skillAnalysisSub: 'เปรียบเทียบทักษะของนักศึกษากับค่าเฉลี่ยของสาขาและค่าเฉลี่ยของคณะ',

  student: 'นักศึกษา',
  facultyAvg: 'เฉลี่ยคณะ',
  facultyAvgShort: 'เฉลี่ยคณะ',

  strongestSkill: 'ทักษะที่แข็งแกร่งที่สุด',
  studentScore: 'คะแนนนักศึกษา',
  overallAverage: 'คะแนนเฉลี่ยรวม',

  skillGapAnalysis: 'การวิเคราะห์ช่องว่างทักษะ',
  skillGapSub: 'ทักษะที่ต่ำกว่าค่าเฉลี่ยของคณะในภาคการศึกษานี้',
  skillGapSubMajor: 'ทักษะที่ต่ำกว่าค่าเฉลี่ยของสาขาที่นักศึกษาคนนี้เรียนในภาคการศึกษานี้',
  belowFacultyAverage: 'ต่ำกว่าค่าเฉลี่ยของคณะ',
  belowMajorAverage: 'ต่ำกว่าค่าเฉลี่ยของสาขา',
  majorAvgShort: 'เฉลี่ยสาขา',
  gapCompareLabel: 'เทียบกับ',
  skillAnalysisSubMajor: 'ทักษะจากกิจกรรมสาขาของนักศึกษา เทียบกับค่าเฉลี่ยของสาขา (ไม่นับกิจกรรมภายนอก)',
  skillAnalysisSubFaculty: 'ทักษะจากกิจกรรมคณะ เทียบกับค่าเฉลี่ยของคณะ (ไม่นับกิจกรรมภายนอก)',
  studentMajorActivities: 'นักศึกษา (กิจกรรมสาขา)',
  studentFacultyActivities: 'นักศึกษา (กิจกรรมคณะ)',
  gapCompareMajor: 'สาขา',
  gapCompareFaculty: 'คณะ',
  studentExternalActivities: 'นักศึกษา (กิจกรรมภายนอก)',
  faculty: 'คณะ',

  recommendation: 'คำแนะนำ:',
  noSignificantGaps: 'ไม่พบช่องว่างทักษะที่สำคัญ',
  noGapSub: 'นักศึกษาคนนี้มีคะแนนเท่ากับหรือสูงกว่าค่าเฉลี่ยของคณะในทั้ง 6 ทักษะ',
  noGapSubMajor: 'นักศึกษาคนนี้มีคะแนนเท่ากับหรือสูงกว่าค่าเฉลี่ยของสาขาในทั้ง 6 ทักษะ',

  periodAll: 'ทั้งปี',
  periodSemester1: 'ภาคการศึกษาที่ 1 (ม.ค.–มิ.ย.)',
  periodSemester2: 'ภาคการศึกษาที่ 2 (ก.ค.–ธ.ค.)',
  yearLabel: 'ปี',

  benchmarkButton: 'มาตรฐาน',
  benchmarkModalTitle: 'ตั้งค่าระดับมาตรฐาน',
  benchmarkModalSubtitle: 'กำหนดเป้าหมายของแต่ละทักษะได้ตั้งแต่ 1.0 ถึง 5.0 และบันทึกลงฐานข้อมูล',
  cancel: 'ยกเลิก',
  saveBenchmark: 'บันทึกมาตรฐาน',
  savingBenchmark: 'กำลังบันทึก...',
  benchmarkRangeError: 'คะแนนมาตรฐานทุกทักษะต้องอยู่ระหว่าง 1.0 ถึง 5.0',

  loadErrorFallback: 'ไม่สามารถโหลดข้อมูลทักษะนักศึกษาได้',
  saveBenchmarkErrorFallback: 'ไม่สามารถบันทึกมาตรฐานได้',

  notAvailable: 'ไม่มีข้อมูล',
  belowScore3: 'ต่ำกว่า 3.0',

  activitiesAttended: 'กิจกรรมที่เข้าร่วม',
  activitiesUnit: 'กิจกรรม',
  joinedPrefix: 'เข้าร่วม',
  idLabel: 'รหัส',

  studentDetailAriaLabel: 'รายละเอียดทักษะของนักศึกษา',
  closeStudentDetails: 'ปิดรายละเอียดนักศึกษา',

  activityHistoryTitle: 'ประวัติกิจกรรมของนักศึกษา',
  activityHistoryAriaLabel: 'ประวัติกิจกรรมของนักศึกษา',
  closeActivityHistory: 'ปิดประวัติกิจกรรม',
  activityHistoryLoading: 'กำลังโหลดประวัติกิจกรรม...',
  activityHistoryError: 'ไม่สามารถโหลดประวัติกิจกรรมได้',
  noActivityHistory: 'นักศึกษาคนนี้ยังไม่มีประวัติกิจกรรม',
  activityNameColumn: 'ชื่อกิจกรรม',
  activityTypeColumn: 'ประเภท',
  activityDateColumn: 'วันที่',
  activityRoleColumn: 'บทบาท',
  activityStatusColumn: 'สถานะ',
  activityTypeFaculty: 'กิจกรรมของคณะ',
  activityTypeExternal: 'กิจกรรมภายนอก',
  roleParticipant: 'ผู้เข้าร่วม',
  roleOrganizer: 'ผู้จัด',
  statusApproved: 'อนุมัติแล้ว',
  statusPending: 'รอดำเนินการ',
  statusRejected: 'ถูกปฏิเสธ',

  skillArtsCultureTraditions: 'ศิลปะ วัฒนธรรม และประเพณี',
  skillVolunteerism: 'จิตอาสา',
  skillAcademics: 'วิชาการ',
  skillInternationalization: 'ความเป็นนานาชาติ',
  skillHealthPromotion: 'การส่งเสริมสุขภาพ',
  skillNatureEnvironmentalConservation: 'ธรรมชาติและการอนุรักษ์สิ่งแวดล้อม',
  skillCreativeLeadership: 'ภาวะผู้นำเชิงสร้างสรรค์',
  skillInnovation: 'นวัตกรรม',
  skillEntrepreneurship: 'ความเป็นผู้ประกอบการ',
  skillPromoteEquality: 'การส่งเสริมความเท่าเทียม',
  skillAcademic: 'ทักษะทางวิชาการ',
  skillNatureEnvironmental: 'ธรรมชาติและสิ่งแวดล้อม',

  growthPlanArtsCultureTraditions: 'เพิ่มกิจกรรมด้านศิลปะ วัฒนธรรม และประเพณีที่ให้นักศึกษามีส่วนร่วมจริง',
  growthPlanVolunteerism: 'เพิ่มกิจกรรมอาสาสมัครและกิจกรรมบริการชุมชนที่มีบทบาทชัดเจน',
  growthPlanAcademics: 'เพิ่มกิจกรรมวิชาการ เวิร์กช็อป และโจทย์ประยุกต์ที่เชื่อมกับการเรียน',
  growthPlanInternationalization: 'เพิ่มกิจกรรมที่ส่งเสริมการทำงานข้ามวัฒนธรรมและการใช้ภาษาต่างประเทศ',
  growthPlanHealthPromotion: 'เพิ่มกิจกรรมส่งเสริมสุขภาพและการดูแลสุขภาวะของนักศึกษา',
  growthPlanNatureEnvironmentalConservation: 'เพิ่มกิจกรรมด้านธรรมชาติ สิ่งแวดล้อม และการอนุรักษ์อย่างต่อเนื่อง',
  growthPlanCreativeLeadership: 'ให้นักศึกษาได้เป็นผู้จัดที่ต้องนำทีมและวางแผนกิจกรรมมากขึ้น',
  growthPlanInnovation: 'เพิ่มบทบาทผู้จัดในแฮกกาธอน โครงการนวัตกรรม และรูปแบบกิจกรรมใหม่ ๆ',
  growthPlanEntrepreneurship: 'เพิ่มกิจกรรมที่ผู้จัดได้ดูแลงบประมาณ ผู้สนับสนุน หรือโครงการธุรกิจขนาดเล็ก',
  growthPlanPromoteEquality: 'เพิ่มกิจกรรมที่ผู้จัดได้ดูแลให้นักศึกษาทุกคนเข้าถึงได้อย่างเท่าเทียม',
  growthPlanAcademic: 'เพิ่มสัมมนา เวิร์กช็อป และกิจกรรมวิชาการที่นักศึกษาเป็นผู้จัดเอง',
  growthPlanNatureEnvironmental: 'เพิ่มโครงการด้านสิ่งแวดล้อมที่นักศึกษาเป็นผู้นำและผู้จัดเอง',

  recommendationArtsCultureTraditions: 'เข้าร่วมกิจกรรมด้านศิลปะ วัฒนธรรม ประเพณี และอัตลักษณ์ชุมชน',
  recommendationVolunteerism: 'เข้าร่วมโครงการอาสาสมัครที่มีหน้าที่ชัดเจนและสร้างผลกระทบต่อชุมชน',
  recommendationAcademics: 'เข้าร่วมเวิร์กช็อปวิชาการ การแข่งขัน หรือกิจกรรมเรียนรู้ผ่านโครงงาน',
  recommendationInternationalization: 'เข้าร่วมกิจกรรมข้ามวัฒนธรรมหรือกิจกรรมนานาชาติ เพื่อฝึกการทำงานร่วมกันระดับโลก',
  recommendationHealthPromotion: 'เข้าร่วมกิจกรรมส่งเสริมสุขภาพและสร้างพฤติกรรมสุขภาวะที่ยั่งยืน',
  recommendationNatureEnvironmentalConservation: 'เข้าร่วมกิจกรรมอนุรักษ์สิ่งแวดล้อมและความยั่งยืน',
  recommendationCreativeLeadership: 'รับบทบาทผู้จัดที่ได้นำทีมหรือวางแผนกิจกรรม',
  recommendationInnovation: 'ช่วยจัดแฮกกาธอนหรือโครงการนวัตกรรม และลองนำเสนอไอเดียใหม่',
  recommendationEntrepreneurship: 'ช่วยดูแลงบประมาณ ผู้สนับสนุน หรือการระดมทุนของกิจกรรม',
  recommendationPromoteEquality: 'ช่วยจัดกิจกรรมที่ทำให้นักศึกษาทุกคนเข้าถึงได้อย่างเท่าเทียม',
  recommendationAcademic: 'ช่วยจัดสัมมนา เวิร์กช็อป หรือกิจกรรมวิชาการ',
  recommendationNatureEnvironmental: 'ช่วยนำหรือจัดโครงการด้านสิ่งแวดล้อมและความยั่งยืน'
 },

  adminApproval: {
    pageTitle: 'การอนุมัติ',
    pageSubtitle: 'จัดการคำขอที่รอการตรวจสอบและอนุมัติจากระบบ',
    statTotalPending: 'รอดำเนินการทั้งหมด',
    statApprovedToday: 'อนุมัติวันนี้',
    statRejectedToday: 'ไม่อนุมัติวันนี้',
    statusTabsAriaLabel: 'สถานะคำขอ',
    pendingTab: 'รอดำเนินการ',
    rejectedTab: 'ถูกปฏิเสธ',
    pendingRequestsHeading: 'รายการที่รอดำเนินการ',
    rejectedRequestsHeading: 'รายการที่ถูกปฏิเสธ',
    filterButton: 'ตัวกรอง',
    sortButton: 'เรียงลำดับ',
    filterAllTypes: 'ทุกประเภท',
    filterSkillValidation: 'การรับรองทักษะ',
    filterSpecialRequest: 'คำขอพิเศษ',
    filterExternalActivity: 'กิจกรรมภายนอก',
    loadingRequests: 'กำลังโหลดข้อมูล...',
    noPendingRequests: 'ไม่มีคำขอที่รอดำเนินการ',
    noRejectedRequests: 'ไม่มีคำขอที่ถูกปฏิเสธ',
    tableHeaderRequesterName: 'ชื่อผู้ขอ',
    tableHeaderRequestType: 'ประเภทคำขอ',
    tableHeaderDateSubmitted: 'วันที่ส่งคำขอ',
    tableHeaderDetails: 'รายละเอียด',
    tableHeaderActions: 'การดำเนินการ',
    idLabel: 'รหัส:',
    viewDetailButton: 'ดูรายละเอียด',
    approveButton: 'อนุมัติ',
    rejectButton: 'ไม่อนุมัติ',
    cancelButton: 'ยกเลิก',
    emptyPlaceholder: '-',
    paginationShowing: 'แสดง',
    paginationOf: 'จาก',
    paginationPendingRequests: 'รายการที่รอดำเนินการ',
    detailModalTitle: 'รายละเอียดคำขอ',
    detailRequesterLabel: 'ผู้ขอ',
    detailRequestTypeLabel: 'ประเภทคำขอ',
    detailFieldLabel: 'รายละเอียด',
    submittedLabel: 'วันที่ส่ง',
    reviewEyebrow: 'กิจกรรมภายนอก',
    loadingShort: 'กำลังโหลด...',
    reviewModalAriaLabel: 'รายละเอียดกิจกรรมภายนอก',
    loadingReviewDetail: 'กำลังโหลดรายละเอียด...',
    studentLabel: 'นักศึกษา',
    activityDetailsLabel: 'รายละเอียดกิจกรรม',
    externalOrganizerLabel: 'ผู้จัดกิจกรรมภายนอก',
    categoryLabel: 'หมวดหมู่',
    roleLabel: 'บทบาท',
    roleOrganizer: 'ผู้จัด',
    roleParticipant: 'ผู้เข้าร่วม',
    dateLabel: 'วันที่',
    locationLabel: 'สถานที่',
    noDescriptionText: 'ไม่มีคำอธิบาย',
    rejectReasonLabel: 'เหตุผลที่ไม่อนุมัติ',
    evidenceLabel: 'หลักฐาน',
    skillMappingLabel: 'Skill Mapping (โดยนักศึกษา)',
    relatedLabel: 'ที่เกี่ยวข้อง',
    staffSkillsLabel: 'ทักษะสายบุคลากร',
    participantSkillsLabel: 'ทักษะผู้เข้าร่วม',
    notRelatedLabel: 'ไม่เกี่ยวข้อง',
    levelPrefix: 'ระดับ',
    confirmApprovalTitle: 'ยืนยันการอนุมัติ',
    rejectActivityTitle: 'ไม่อนุมัติกิจกรรม',
    confirmApprovalAriaLabel: 'ยืนยันการอนุมัติ',
    rejectWithCommentAriaLabel: 'ไม่อนุมัติพร้อมความคิดเห็น',
    confirmApprovalExternalText: 'ต้องการอนุมัติกิจกรรมนี้ใช่หรือไม่? กิจกรรมและ Skill Mapping ที่นักศึกษาตั้งไว้ จะถูกนับรวมในหน้า My Activities ของนักศึกษา',
    confirmApprovalGenericText: 'ต้องการอนุมัติคำขอนี้ใช่หรือไม่?',
    loadingSkillMapping: 'กำลังโหลด Skill Mapping...',
    rejectCommentLabel: 'ความคิดเห็น / เหตุผลที่ไม่อนุมัติ *',
    rejectCommentPlaceholder: 'อธิบายว่าทำไมไม่อนุมัติ หรือนักศึกษาต้องแก้ไขอะไร เช่น ไฟล์หลักฐานไม่ชัดเจน กรุณาแนบใหม่',
    rejectCommentHint: 'ความคิดเห็นนี้จะส่งเป็นการแจ้งเตือน (Notification) ให้นักศึกษาเห็นทันที',
    confirmApproveButton: 'ยืนยันอนุมัติ',
    confirmRejectButton: 'ยืนยันไม่อนุมัติ',
    loadDetailError: 'โหลดรายละเอียดไม่สำเร็จ',
    rejectReasonRequired: 'กรุณาระบุเหตุผลที่ไม่อนุมัติ หรือสิ่งที่นักศึกษาต้องแก้ไข',
    saveFailed: 'บันทึกไม่สำเร็จ',
    resultApprovedTitle: 'อนุมัติสำเร็จ',
    resultApprovedMessage: "อนุมัติกิจกรรม '{name}' เรียบร้อยแล้ว",
    resultRejectedTitle: 'ไม่อนุมัติสำเร็จ',
    resultRejectedMessage: "ปฏิเสธกิจกรรม '{name}' เรียบร้อยแล้ว",
    resultOkButton: 'ตกลง',
    loadRequestsError: 'โหลดข้อมูลไม่สำเร็จ'
  },

  studentActivities: {
    openEvidenceFailed: 'เปิดไฟล์หลักฐานไม่สำเร็จ',
    pageTitle: 'กิจกรรมของฉัน',
    pageSubtitle: 'กิจกรรมของคณะที่คุณเข้าร่วมและกิจกรรมภายนอกที่ได้รับอนุมัติ',
    searchPlaceholder: 'ค้นหากิจกรรมของฉัน...',
    clearSearch: 'ล้างคำค้นหา',
    totalActivitiesLabel: 'กิจกรรมทั้งหมด',
    allTab: 'ทั้งหมด',
    facultyActivitiesTab: 'กิจกรรมคณะ',
    externalActivitiesTab: 'กิจกรรมภายนอก',
    mySubmissionsTab: 'รายการที่ส่ง',
    majorActivitiesTab: 'กิจกรรมของสาขา',
    majorActivityLabel: 'กิจกรรมของสาขา',
    joinedBadge: 'เข้าร่วมแล้ว',
    notJoinedLabel: 'ยังไม่ได้เข้าร่วม',
    notJoinedTitle: 'คุณยังไม่ได้เข้าร่วมกิจกรรมนี้',
    notJoinedText: 'กิจกรรมนี้จัดโดยสาขาของคุณ มีผู้เข้าร่วมแล้ว {count} คน ติดต่อผู้จัดกิจกรรมหากต้องการเข้าร่วม',
    noMajorActivitiesLabel: 'สาขาของคุณยังไม่มีกิจกรรม',
    noMajorLabel: 'โปรไฟล์ของคุณยังไม่มีสาขา จึงยังแสดงกิจกรรมของสาขาไม่ได้',
    filterByDateLabel: 'กรองตามวันที่',
    clearLabel: 'ล้างค่า',
    loadingLabel: 'กำลังโหลดกิจกรรม...',
    loadActivitiesErrorLabel: 'ไม่สามารถโหลดข้อมูลกิจกรรมได้',
    statusActive: 'กำลังดำเนินการ',
    statusCompleted: 'เสร็จสิ้น',
    statusCancelled: 'ยกเลิก',
    statusApproved: 'อนุมัติแล้ว',
    statusPending: 'รอดำเนินการ',
    statusRejected: 'ไม่อนุมัติ',
    externalActivityLabel: 'กิจกรรมภายนอก',
    facultyActivityLabel: 'กิจกรรมคณะ',
    roleOrganizer: 'ผู้จัดกิจกรรม',
    roleParticipant: 'ผู้เข้าร่วม',
    rejectReasonPrefix: 'เหตุผลที่ไม่อนุมัติ:',
    editLabel: 'แก้ไข',
    deleteLabel: 'ลบ',
    deletingLabel: 'กำลังลบ...',
    deleteSubmissionConfirm: 'ลบคำขอ "{title}"?\n\nไฟล์หลักฐานจะถูกลบด้วย และกู้คืนไม่ได้',
    deleteSubmissionFailed: 'ลบคำขอไม่สำเร็จ',
    detailsButtonLabel: 'รายละเอียด',
    viewActivityDetailsAriaLabel: 'ดูรายละเอียดกิจกรรม',
    noActivitiesFoundTitle: 'ไม่พบกิจกรรม',
    tryAnotherLabel: 'ลองค้นหาชื่อกิจกรรมหรือวันที่อื่น',
    noSubmissionsYetLabel: 'ยังไม่มีการส่งกิจกรรมภายนอก',
    noApprovedActivitiesYetLabel: 'ยังไม่มีกิจกรรมคณะหรือกิจกรรมภายนอกที่ได้รับอนุมัติ',
    loadMoreLabel: 'โหลดกิจกรรมเพิ่มเติม',
    idLabel: 'รหัส:',
    closeDetailsAriaLabel: 'ปิดรายละเอียด',
    activityDetailsHeading: 'รายละเอียดกิจกรรม',
    categoryLabel: 'หมวดหมู่',
    dateLabel: 'วันที่',
    sourceDetailLabel: 'แหล่งที่มา',
    roleLabel: 'บทบาท',
    locationLabel: 'สถานที่',
    organizerLabel: 'ผู้จัดกิจกรรม',
    activityDescriptionHeading: 'คำอธิบายกิจกรรม',
    studentReflectionHeading: 'การสะท้อนคิดของนักศึกษา',
    noDescriptionProvided: 'ไม่มีคำอธิบาย',
    viewEvidenceLabel: 'ดูหลักฐาน',
    skillsHeading: 'ทักษะ',
    skillMappingHeading: 'การจับคู่ทักษะ',
    levelLabel: 'ระดับ',
    noRelatedSkillsLabel: 'ไม่มีทักษะที่เกี่ยวข้อง',
    currentStatusLabel: 'สถานะปัจจุบัน',
    waitingForReviewTitle: 'รอการตรวจสอบ',
    waitingForReviewText: 'รายการนี้กำลังรอการตรวจสอบจากผู้ดูแลระบบ',
    activityNotApprovedTitle: 'กิจกรรมไม่ได้รับการอนุมัติ',
    activityNotApprovedFallbackText: 'กิจกรรมนี้ไม่ได้รับการอนุมัติ',
    approvedByAdminTitle: 'ได้รับการอนุมัติจากผู้ดูแลระบบ',
    approvedByAdminText: 'กิจกรรมภายนอกนี้และการจับคู่ทักษะของคุณได้รับการตรวจสอบและอนุมัติแล้ว',
    activityCancelledTitle: 'กิจกรรมถูกยกเลิก',
    activityCancelledText: 'กิจกรรมของคณะนี้ถูกยกเลิกแล้ว',
    activityCompletedTitle: 'กิจกรรมเสร็จสิ้นแล้ว',
    registeredTitle: 'ลงทะเบียนแล้ว',
    listedAsRolePrefix: 'คุณถูกบันทึกเป็น',
    listedAsRoleSuffix: 'ในกิจกรรมของคณะนี้'
  },

  adminCreateActivity: {
    eyebrowActivityManagement: 'การจัดการกิจกรรม',
    pageTitle: 'สร้างกิจกรรมใหม่',
    stepActivityInfoTitle: 'ข้อมูลกิจกรรม',
    stepActivityInfoSubtitle: 'รายละเอียดกิจกรรม',
    stepAttachSkillsTitle: 'แนบ Skill',
    stepAttachSkillsSubtitle: 'กำหนดระดับ Skill',
    basicInfoTitle: 'ข้อมูลพื้นฐาน',
    basicInfoSubtitle: 'ข้อมูลหลักที่ใช้แสดงในหน้ากิจกรรม',
    activityTypeLabel: 'ประเภทกิจกรรม',
    selectActivityTypePlaceholder: 'เลือกประเภทกิจกรรม',
    customActivityTypePlaceholder: 'โปรดระบุประเภทกิจกรรม',
    activityNameLabel: 'ชื่อกิจกรรม (ไทย/อังกฤษ)',
    activityNamePlaceholder: 'เช่น Bio-Tech Innovations 2026',
    scheduleTitle: 'กำหนดการ',
    scheduleSubtitle: 'เลือกวันที่เริ่มต้น / สิ้นสุดของกิจกรรม',
    startDateLabel: 'วันที่เริ่มต้น',
    startDateBadge: 'วันที่เริ่มต้น',
    endDateLabel: 'วันที่สิ้นสุด',
    endDateBadge: 'วันที่สิ้นสุด',
    selectDatePlaceholder: 'เลือกวันที่',
    calendarHeaderSelectStart: 'เลือกวันที่เริ่มต้น',
    calendarHeaderSelectEnd: 'เลือกวันที่สิ้นสุด',
    calendarFooterHintStart: 'เลือกได้ทุกวันที่ต้องการ',
    calendarFooterHintEnd: 'วันสิ้นสุดต้องไม่ก่อนวันเริ่มต้น',
    todayButton: 'วันนี้',
    orgPersonnelTitle: 'หน่วยงานและบุคลากร',
    orgPersonnelSubtitle: 'ระบุหน่วยงาน ผู้รับผิดชอบ และสถานที่',
    departmentLabel: 'หน่วยงานที่จัด (ภาควิชา/คณะ)',
    departmentPlaceholder: 'เช่น Physics Department',
    responsiblePersonLabel: 'ผู้รับผิดชอบหลัก',
    responsiblePersonPlaceholder: 'ค้นหาชื่อบุคลากร...',
    advisorLabel: 'อาจารย์ที่ปรึกษา (อาจารย์ผู้รับผิดชอบ)',
    advisorPlaceholder: 'ชื่ออาจารย์ที่ปรึกษา',
    locationLabel: 'สถานที่',
    locationPlaceholder: 'เช่น Room 402, Science Building 3',
    additionalDetailsTitle: 'รายละเอียดเพิ่มเติม',
    additionalDetailsSubtitle: 'ระบุวัตถุประสงค์ ผลลัพธ์ และกลุ่มเป้าหมาย',
    descriptionLabel: 'รายละเอียดกิจกรรม',
    descriptionPlaceholder: 'ระบุวัตถุประสงค์ ผลลัพธ์ที่คาดหวัง และกลุ่มเป้าหมาย...',
    tipsTitle: 'ก่อนกดถัดไป',
    tipsSubtitle: 'ตรวจสอบข้อมูลสำคัญให้ครบก่อนกำหนด Skill ของกิจกรรม',
    tipNameAndType: 'ชื่อและประเภทกิจกรรม',
    tipDates: 'วันที่เริ่ม / สิ้นสุด',
    tipLocation: 'สถานที่จัดกิจกรรม',
    skillsEyebrow: 'แนบ Skill',
    skillsSectionTitle: 'กำหนด Skill ของกิจกรรม',
    skillsForStaffDescription: 'Skill สำหรับผู้จัดกิจกรรม',
    skillsForParticipantDescription: 'Skill สำหรับผู้เข้าร่วมกิจกรรม',
    staffLabel: 'ผู้จัดกิจกรรม',
    participantLabel: 'ผู้เข้าร่วม',
    cancelButton: 'ยกเลิก',
    backButton: 'ย้อนกลับ',
    continueButton: 'ถัดไป',
    creatingButton: 'กำลังสร้าง...',
    createActivityButton: 'สร้างกิจกรรม',
    weekDays: ['จ', 'อ', 'พ', 'พฤ', 'ศ', 'ส', 'อา'],
    validateOtherActivityTypeRequired: 'กรุณาระบุประเภทกิจกรรมอื่นๆ',
    validateRequiredFields: 'กรุณากรอกข้อมูลที่มีเครื่องหมาย * ให้ครบ',
    validateEndDateBeforeStart: 'วันที่สิ้นสุดต้องไม่ก่อนวันที่เริ่มต้น',
    backendConnectionError: 'เชื่อมต่อ Backend ไม่ได้',
    backendConnectionErrorHint: 'กรุณาตรวจว่า uvicorn ยังรันอยู่',
    createActivityError: 'ไม่สามารถสร้างกิจกรรมได้'
  },

  adminStudentActivities: {
    downloadTemplateButton: 'ดาวน์โหลด Template',
    downloadTemplateError: 'ดาวน์โหลด Template ไม่สำเร็จ กรุณาลองใหม่',
    activityNameLabel: 'ชื่อกิจกรรม *',
    activityNamePlaceholder: 'ชื่อกิจกรรม',
    activityTypeLabel: 'ประเภทกิจกรรม *',
    activityTypePlaceholder: 'ประเภทกิจกรรม',
    addingStudentLoading: 'กำลังเพิ่ม...',
    addStudentAction: 'เพิ่มนักศึกษา',
    addStudentFailedDefault: 'เพิ่มนักศึกษาไม่สำเร็จ',
    addStudentModalEyebrow: 'เพิ่มนักศึกษา',
    addStudentModalTitle: 'เพิ่มนักศึกษาด้วยตนเอง',
    addStudentSuccessMessage: 'เพิ่มนักศึกษาเข้ากิจกรรมสำเร็จ',
    addStudentValidationError: 'กรุณากรอกรหัสนักศึกษา ชื่อ นามสกุล อีเมล สาขาวิชา และ Role ให้ครบ',
    advisorLabel: 'อาจารย์ที่ปรึกษา',
    applyFiltersButton: 'ใช้ตัวกรอง',
    backButton: 'ย้อนกลับ',
    backendConnectionError: 'ไม่สามารถเชื่อมต่อ Backend ได้',
    cancelActivityMenuItem: 'ยกเลิกกิจกรรม',
    cancelButton: 'ยกเลิก',
    changeStatusFailedDefault: 'เปลี่ยนสถานะกิจกรรมไม่สำเร็จ',
    confirmImportButton: 'ยืนยัน Import ({count})',
    createActivityButton: 'สร้างกิจกรรมใหม่',
    deleteActivityConfirm: 'ต้องการลบกิจกรรม "{name}" หรือไม่?\nการลบจะลบสมาชิกและ Skill ที่ผูกกับกิจกรรมนี้ด้วย',
    deleteActivityFailedDefault: 'ลบกิจกรรมไม่สำเร็จ',
    deleteActivityMenuItem: 'ลบกิจกรรม',
    departmentLabel: 'หน่วยงาน',
    descriptionLabel: 'รายละเอียด',
    dropzoneHeading: 'ลากไฟล์มาวาง หรือคลิกเพื่อเลือกไฟล์',
    dropzoneSubtext: 'รองรับไฟล์ .csv, .xlsx และ .xls',
    editActivityFailedDefault: 'แก้ไขกิจกรรมไม่สำเร็จ',
    editActivityMenuItem: 'แก้ไขกิจกรรม',
    editActivityTitle: 'แก้ไขกิจกรรม',
    editActivityValidationError: 'กรุณากรอกชื่อ ประเภท วันเวลา ผู้รับผิดชอบ และสถานที่ให้ครบ',
    emailLabel: 'อีเมล *',
    emailPlaceholder: 'student@cmu.ac.th',
    emptyActivitiesTableText: 'ยังไม่มีกิจกรรม หรือไม่พบกิจกรรมที่ตรงกับเงื่อนไข',
    endDateTimeLabel: 'วันที่ / เวลาสิ้นสุด *',
    fileReadFailedDefault: 'ไม่สามารถอ่านไฟล์ได้',
    filterAllCategoriesOption: 'ทุกหมวดหมู่',
    filterCategoryLabel: 'หมวดหมู่',
    filterClearDate: 'ล้างวันที่',
    filterDateFromLabel: 'ตั้งแต่วันที่',
    filterDateToLabel: 'ถึงวันที่',
    filterDatePlaceholder: 'เลือกวันที่',
    filterSearchActivityLabel: 'ค้นหากิจกรรม',
    filterSearchActivityPlaceholder: 'ชื่อกิจกรรม...',
    filterToday: 'วันนี้',
    firstNameLabel: 'ชื่อ *',
    firstNamePlaceholder: 'ชื่อ',
    hideDetailsText: 'ซ่อนรายละเอียด',
    importFailedDefault: 'Import ไม่สำเร็จ',
    importFromFileEyebrow: 'นำเข้าจากไฟล์',
    importFromFileMenuItem: 'นำเข้าจากไฟล์',
    importDuplicateStudentId: 'รหัสนักศึกษาซ้ำกับแถวอื่นในรายการ',
    importingLoadingText: 'กำลังนำเข้า...',
    importInvalidRole: 'Role ต้องเป็น participant หรือ organizer',
    importIssuesHeading: 'ปัญหาที่พบในการนำเข้า',
    importIssuesSubtext: 'แก้ไขได้ในตารางด้านล่าง ถ้าไม่แก้ รายการเหล่านี้จะถูกข้ามตอน Confirm Import',
    importMissingEmail: 'ไม่มีอีเมล',
    importMissingFirstName: 'ไม่มีชื่อ',
    importMissingLastName: 'ไม่มีนามสกุล',
    importMissingStudentId: 'ไม่มีรหัสนักศึกษา',
    importPreviewEyebrow: 'ตัวอย่างการนำเข้า',
    importStudentListTitle: 'นำเข้ารายชื่อนักศึกษา',
    importSuccessDuplicateSuffix: ' (ข้ามข้อมูลซ้ำ {count} คน)',
    importSuccessIssueSuffix: ' • ข้ามข้อมูลที่มีปัญหา {count} รายการ',
    importSuccessMessage: 'Import สำเร็จ {count} คน',
    invalidEmailFormat: 'รูปแบบอีเมลไม่ถูกต้อง',
    issueStatusLabel: 'มีปัญหา',
    lastNameLabel: 'นามสกุล *',
    lastNamePlaceholder: 'นามสกุล',
    loadingAriaLabel: 'กำลังโหลดกิจกรรม',
    locationLabel: 'สถานที่ *',
    majorLabel: 'สาขาวิชา *',
    manageActivityEyebrow: 'จัดการกิจกรรม',
    manageButton: 'จัดการ',
    markAsCompletedMenuItem: 'ทำเครื่องหมายว่าเสร็จสิ้น',
    noRelatedSkillsText: 'ไม่มี Skill ที่เกี่ยวข้อง',
    noValidImportDataError: 'ไม่มีข้อมูลที่พร้อม Import กรุณาตรวจสอบ Issues ก่อน',
    organizerLabel: 'ผู้จัด',
    paginationOf: 'จาก',
    paginationShowing: 'แสดง',
    participantLabel: 'ผู้เข้าร่วม',
    participantSkillsHeading: 'Skill ของผู้เข้าร่วม',
    previewEditHint: 'แก้ไขข้อมูลในตารางได้ก่อนนำเข้า ข้อมูลจะถูกบันทึกเมื่อกด ยืนยัน Import เท่านั้น',
    previewFoundLabel: 'พบข้อมูล',
    previewImportButton: 'ดูตัวอย่างก่อนนำเข้า',
    previewIssueNote: '{count} รายการมีปัญหาและจะไม่ถูกนำเข้าถ้าไม่แก้ไข ส่วนรายการที่เป็น Ready ยังสามารถ Confirm Import ได้ตามปกติ',
    previewIssueRowLabel: 'แถวที่',
    previewIssuesLabel: 'รายการที่มีปัญหา',
    previewReadyLabel: 'พร้อมนำเข้า',
    previewTableEmail: 'อีเมล',
    previewTableFirstName: 'ชื่อ',
    previewTableLastName: 'นามสกุล',
    previewTableMajor: 'สาขาวิชา',
    previewTableRole: 'Role',
    previewTableStatus: 'สถานะ',
    previewTableStudentId: 'รหัสนักศึกษา',
    quickSearchPlaceholder: 'ค้นหากิจกรรมอย่างรวดเร็ว...',
    readingLoadingText: 'กำลังอ่านไฟล์...',
    readyStatusLabel: 'พร้อม',
    removeFileTooltip: 'ลบไฟล์',
    reopenActivityMenuItem: 'เปิดกิจกรรมอีกครั้ง',
    responsiblePersonLabel: 'ผู้รับผิดชอบ *',
    reviewParticipantsTitle: 'ตรวจสอบผู้เข้าร่วม',
    roleFieldLabel: 'Role *',
    saveChangesButton: 'บันทึกการเปลี่ยนแปลง',
    savingLoadingText: 'กำลังบันทึก...',
    selectFileFirstError: 'กรุณาเลือกไฟล์ CSV หรือ Excel ก่อน',
    selectMajorPlaceholder: 'เลือกสาขาวิชา',
    selectRolePlaceholder: 'เลือก Role',
    showDetailsText: 'กดดูรายละเอียด',
    skillLevelLabel: 'ระดับ',
    skillsLabel: 'Skill',
    skillsToggleLabel: 'Skill',
    staffLabel: 'เจ้าหน้าที่',
    staffSkillsHeading: 'Skill ของเจ้าหน้าที่',
    startDateTimeLabel: 'วันที่ / เวลาเริ่ม *',
    statusActive: 'กำลังดำเนินการ',
    statusCancelled: 'ยกเลิกแล้ว',
    statusCompleted: 'เสร็จสิ้น',
    statusFieldLabel: 'สถานะ',
    studentAlreadyInActivity: 'นักศึกษาคนนี้มีอยู่ในกิจกรรมแล้ว',
    studentIdLabel: 'รหัสนักศึกษา *',
    studentIdPlaceholder: 'เช่น 670510001',
    studentSearchPlaceholder: 'พิมพ์รหัสนักศึกษาหรือชื่อเพื่อค้นหา',
    studentLookupLoading: 'กำลังค้นหา...',
    studentIdNotFoundError: 'ไม่พบรหัสนักศึกษานี้ในระบบ',
    facultyLabel: 'คณะ',
    noMajorLabel: 'ไม่มีสาขา',
    summaryActiveActivities: 'กิจกรรมที่กำลังดำเนินการ',
    summaryParticipantsMonth: 'ผู้เข้าร่วม (เดือนนี้)',
    summaryPendingEvaluations: 'คำขอที่รออนุมัติ',
    tableHeaderActivityName: 'ชื่อกิจกรรม',
    sortByStartDate: 'เรียงตามวันที่เริ่ม',
    sortByLatest: 'เรียงตามรายการล่าสุด',
    sortAriaLabel: 'เรียงลำดับกิจกรรม',
    sortDirectionAsc: 'เก่าไปใหม่ (กดเพื่อสลับ)',
    sortDirectionDesc: 'ใหม่ไปเก่า (กดเพื่อสลับ)',
    tableHeaderDetails: 'รายละเอียด',
    tableHeaderEndDate: 'วันที่สิ้นสุด',
    tableHeaderManageActivity: 'จัดการกิจกรรม',
    tableHeaderManageParticipants: 'จัดการผู้เข้าร่วม',
    tableHeaderOrganizer: 'ผู้จัดงาน',
    tableHeaderParticipants: 'ผู้เข้าร่วม',
    tableHeaderStartDate: 'วันที่เริ่ม',
    unknownStudentFallback: 'ไม่ทราบชื่อนักศึกษา',
    unsupportedFileTypeError: 'รองรับเฉพาะไฟล์ .csv, .xlsx และ .xls เท่านั้น',
    viewDetailButton: 'ดูรายละเอียด',
    weekdayFri: 'ศ',
    weekdayMon: 'จ',
    weekdaySat: 'ส',
    weekdaySun: 'อา',
    weekdayThu: 'พฤ',
    weekdayTue: 'อ',
    weekdayWed: 'พ'
  },

  studentExternalActivity: {
    editTitle: 'แก้ไขและส่งกิจกรรมใหม่',
    addTitle: 'เพิ่มกิจกรรมภายนอก',
    editSubtitle: 'แก้ไขข้อมูลกิจกรรมที่ถูกไม่อนุมัติ แล้วส่งใหม่อีกครั้งเพื่อให้แอดมินตรวจสอบ',
    addSubtitle: 'ส่งกิจกรรมที่เข้าร่วมภายนอกคณะ พร้อมหลักฐานและ Skill Mapping เพื่อให้แอดมินตรวจสอบและอนุมัติ',
    activityDetailsHeading: 'รายละเอียดกิจกรรม',
    activityNameLabel: 'ชื่อกิจกรรม',
    activityNamePlaceholder: 'กรอกชื่อกิจกรรมที่เข้าร่วม',
    organizerLabel: 'ผู้จัดกิจกรรมภายนอก',
    organizerPlaceholder: 'หน่วยงาน / องค์กรที่จัดกิจกรรม',
    categoryLabel: 'ประเภทกิจกรรม',
    selectCategoryOption: 'เลือกประเภทกิจกรรม',
    otherCategoryModalTitle: 'โปรดระบุประเภทของกิจกรรม',
    otherCategoryInputPlaceholder: 'พิมพ์ประเภทกิจกรรมของคุณ',
    otherCategoryConfirmButton: 'ยืนยัน',
    otherCategoryCancelButton: 'ยกเลิก',
    otherCategoryRequiredError: 'กรุณาระบุประเภทกิจกรรม',
    otherCategoryDisplayLabel: 'ประเภทที่ระบุ',
    otherCategoryEditButton: 'แก้ไข',
    roleLabel: 'บทบาทของคุณ',
    selectRoleOption: 'เลือกบทบาท',
    descriptionLabel: 'รายละเอียดกิจกรรม / สิ่งที่ได้เรียนรู้',
    descriptionPlaceholder: 'อธิบายสิ่งที่คุณทำและสิ่งที่ได้เรียนรู้จากกิจกรรมนี้...',
    startDateLabel: 'วันที่เริ่มต้น',
    startDatePlaceholder: 'เลือกวันที่เริ่มต้น',
    endDateLabel: 'วันที่สิ้นสุด',
    endDatePlaceholder: 'เลือกวันที่สิ้นสุด',
    locationLabel: 'สถานที่',
    locationPlaceholder: 'ระบุสถานที่หรือลิงก์ออนไลน์',
    uploadEvidenceLabel: 'แนบหลักฐาน',
    uploadEvidenceHint: 'เกียรติบัตร หรือรูปถ่ายขณะเข้าร่วม · แนบได้สูงสุด {max} ไฟล์ · รองรับ JPG, PNG, PDF ไฟล์ละไม่เกิน 5MB',
    chooseFileButton: 'คลิกเพื่อเลือกไฟล์',
    currentEvidenceLabel: 'หลักฐานปัจจุบัน',
    addMoreFilesButton: 'เพิ่มไฟล์',
    newEvidenceLabel: 'ไฟล์ใหม่',
    evidenceListHeading: 'ไฟล์หลักฐาน',
    evidenceCountLabel: '{count}/{max} ไฟล์',
    evidenceLimitReached: 'แนบครบ {max} ไฟล์แล้ว ลบไฟล์ออกก่อนถ้าต้องการเพิ่มไฟล์อื่น',
    evidenceLimitError: 'แนบไฟล์หลักฐานได้สูงสุด {max} ไฟล์ต่อคำขอ',
    removeFileAriaLabel: 'ลบไฟล์',
    submittingButton: 'กำลังส่ง...',
    resubmittingButton: 'กำลังส่งใหม่...',
    submitButton: 'ส่งเพื่อขออนุมัติ',
    resubmitButton: 'ส่งใหม่เพื่อขออนุมัติ',
    skillMappingHeading: 'Skill Mapping',
    skillMappingSubtitle: 'ประเมินระดับ Skill ที่คุณพัฒนาขึ้น (1-5)',
    participantTab: 'Participant',
    staffTab: 'Staff',
    skillsFieldLabel: 'ทักษะที่ได้รับ',
    skillsFieldHint: 'ชุดทักษะเปลี่ยนตามบทบาท',
    viewSkillsButton: 'ดูทักษะ',
    adjustSkillsButton: 'ปรับระดับทักษะ',
    evidenceCardHeading: 'หลักฐานการเข้าร่วม',
    skillsSelectedSingular: 'เลือกแล้ว {count} ทักษะ',
    skillsSelectedPlural: 'เลือกแล้ว {count} ทักษะ',
    skillsNoneSelected: 'ยังไม่ได้เลือกทักษะ',
    skillsModalSave: 'บันทึก',
    skillsModalCancel: 'ยกเลิก',
    skillsModalClose: 'ปิด',
    loadEditFailed: 'โหลดข้อมูลกิจกรรมที่จะแก้ไขไม่สำเร็จ',
    editNotFound: 'ไม่พบกิจกรรมที่ต้องการแก้ไข หรือกิจกรรมนี้ไม่สามารถแก้ไขได้',
    fileTypeError: 'ไฟล์หลักฐานต้องเป็น .jpg, .jpeg, .png หรือ .pdf',
    fileEmptyError: 'ไฟล์หลักฐานว่าง',
    fileSizeError: 'ไฟล์หลักฐานต้องมีขนาดไม่เกิน 5MB',
    requiredFieldsError: 'กรุณากรอกข้อมูลที่มีเครื่องหมาย * ให้ครบ',
    dateRangeError: 'วันที่สิ้นสุดต้องไม่อยู่ก่อนวันที่เริ่มต้น',
    skillRequiredError: 'กรุณาเลือกทักษะที่เกี่ยวข้องอย่างน้อย 1 ทักษะ (กดปุ่ม "ปรับระดับทักษะ")',
    evidenceRequiredError: 'กรุณาแนบไฟล์หลักฐาน (เกียรติบัตร หรือรูปถ่าย)',
    submitFailedFallback: 'ส่งกิจกรรมไม่สำเร็จ',
    confirmSubmitTitle: 'ยืนยันการส่งคำขอ',
    confirmSubmitMessage: "คุณต้องการส่งกิจกรรม '{name}' เพื่อรอการอนุมัติใช่หรือไม่?",
    confirmResubmitTitle: 'ยืนยันการส่งคำขออีกครั้ง',
    confirmResubmitMessage: "คุณต้องการแก้ไขและส่งกิจกรรม '{name}' อีกครั้งเพื่อรอการอนุมัติใช่หรือไม่?",
    confirmCancelButton: 'ยกเลิก',
    confirmSubmitButton: 'ยืนยัน',
    connectionError: 'เชื่อมต่อ Backend ไม่ได้'
  },

  studentSkills: {
    loading: 'กำลังโหลดข้อมูลทักษะ...',
    retry: 'ลองใหม่',
    title: 'ทักษะของฉัน',
    year: 'ปี',
    radarChartTitle: 'ภาพรวมทักษะ - แผนภูมิเรดาร์',
    skillRadar: 'เรดาร์ทักษะ',
    noDataInPeriod: 'ยังไม่มีข้อมูลทักษะในช่วงเวลานี้',
    activitiesUsedTitle: 'กิจกรรมที่นำมาคำนวณทักษะ',
    activitiesUnit: 'กิจกรรม',
    tableActivityName: 'ชื่อกิจกรรม',
    tableDescription: 'รายละเอียด',
    tableSkillsGained: 'ทักษะที่ได้รับ',
    tableDate: 'วันที่',
    tableStatus: 'สถานะ',
    noActivityData: 'ไม่มีข้อมูลกิจกรรม',
    noActivityDataSubtitle: 'กิจกรรมที่ถูกนำมาคำนวณทักษะจะแสดงที่นี่',
    loadError: 'โหลดข้อมูลทักษะไม่สำเร็จ',
    connectionError: 'เชื่อมต่อ Backend ไม่ได้',
    skillTrackLabel: 'ชุด Skill',
    participantSkillsOption: 'Skill ผู้เข้าร่วม',
    staffSkillsOption: 'Skill ผู้จัด (Staff)',
    staffTrackHint: 'Skill ผู้จัดคำนวณจากกิจกรรมที่คุณเป็นผู้จัด (Staff) เท่านั้น',
    radarChartTitleStaff: 'ภาพรวม Skill ผู้จัด (Staff) - แผนภูมิเรดาร์',
    noDataInPeriodStaff: 'ยังไม่มีข้อมูล Skill ผู้จัดในช่วงเวลานี้',
    activitiesUsedTitleStaff: 'กิจกรรมที่เป็นผู้จัด (Staff) ที่นำมาคำนวณ Skill',
    noActivityDataStaff: 'ไม่มีกิจกรรมที่เป็นผู้จัดในช่วงเวลานี้',
    noActivityDataSubtitleStaff: 'กิจกรรมที่คุณเป็นผู้จัด (Staff) จะแสดงที่นี่',
    comparisonLabel: 'เปรียบเทียบกับ',
    comparisonMajorOption: 'กิจกรรมสาขา',
    comparisonFacultyOption: 'กิจกรรมคณะ',
    comparisonMajorHint: 'เปรียบเทียบทักษะจากกิจกรรมของสาขาคุณ กับค่าเฉลี่ยของนักศึกษาในสาขาเดียวกัน (ไม่นับกิจกรรมภายนอก)',
    comparisonFacultyHint: 'เปรียบเทียบทักษะจากกิจกรรมของคณะ กับค่าเฉลี่ยของนักศึกษาทั้งคณะ (ไม่นับกิจกรรมภายนอก)',
    comparisonNoMajor: 'โปรไฟล์ของคุณยังไม่มีสาขา จึงยังเปรียบเทียบกับสาขาไม่ได้',
    mySkillsMajorLegend: 'ทักษะของฉัน (กิจกรรมสาขา)',
    mySkillsFacultyLegend: 'ทักษะของฉัน (กิจกรรมคณะ)',
    majorAverageLegend: 'ค่าเฉลี่ยของสาขา',
    facultyAverageLegend: 'ค่าเฉลี่ยของคณะ',
    scopeMajor: 'สาขา',
    scopeFaculty: 'คณะ',
    scopeExternal: 'ภายนอก',
    scopeOtherMajor: 'สาขาอื่น',
    comparisonExternalOption: 'กิจกรรมภายนอก',
    comparisonExternalHint: 'แสดงทักษะจากกิจกรรมภายนอกที่ได้รับอนุมัติแล้วของคุณ',
    mySkillsExternalLegend: 'ทักษะของฉัน (กิจกรรมภายนอก)',
    statusActive: 'กำลังดำเนินการ',
    statusCompleted: 'เสร็จสิ้น',
    statusApproved: 'อนุมัติแล้ว',
    statusPending: 'รอดำเนินการ',
    statusRejected: 'ถูกปฏิเสธ',
    statusCancelled: 'ยกเลิกแล้ว'
  },

  adminParticipantDetails: {
    eyebrowActivityManagement: 'การจัดการกิจกรรม',
    pageTitle: 'รายละเอียดผู้เข้าร่วม',
    pageSubtitle: 'ตรวจสอบและแก้ไขข้อมูลผู้เข้าร่วมกิจกรรม',
    backButton: 'กลับไปหน้ากิจกรรม',
    activityLabel: 'กิจกรรม',
    participantsLabel: 'ผู้เข้าร่วม',
    organizersLabel: 'ผู้จัดกิจกรรม',
    totalMembersLabel: 'สมาชิกทั้งหมด',
    activityDetailsLabel: 'รายละเอียดกิจกรรม',
    typeLabel: 'ประเภท',
    dateLabel: 'วันที่',
    locationLabel: 'สถานที่',
    responsibleLabel: 'ผู้รับผิดชอบ',
    descriptionLabel: 'รายละเอียด',
    noDescriptionText: 'ไม่มีรายละเอียดเพิ่มเติม',
    readMoreButton: 'อ่านเพิ่มเติม',
    skillsGainedTitle: 'Skill ที่ได้รับตามบทบาท',
    skillsGainedSubtitle: 'ระดับ Skill ที่สมาชิกแต่ละคนจะได้รับจากกิจกรรมนี้ ขึ้นอยู่กับบทบาท',
    participantSkillSetLabel: 'Skill ของผู้เข้าร่วม',
    staffSkillSetLabel: 'Skill ของเจ้าหน้าที่',
    skillLevelLabel: 'ระดับ',
    noSkillsForRoleText: 'ยังไม่ได้กำหนด Skill สำหรับบทบาทนี้',
    studentsInActivityTitle: 'นักศึกษาในกิจกรรม',
    studentsInActivitySubtitle: 'กด Edit เพื่อแก้ไขข้อมูลทั้งแถวได้พร้อมกัน หรือกด นำออก เพื่อเอานักศึกษาออกจากกิจกรรมนี้',
    studentsCountSuffix: 'คน',
    loadingText: 'กำลังโหลดข้อมูล...',
    studentIdHeader: 'รหัสนักศึกษา',
    studentNameHeader: 'ชื่อนักศึกษา',
    facultyHeader: 'คณะ',
    majorHeader: 'สาขาวิชา',
    roleHeader: 'บทบาท',
    actionsHeader: 'การจัดการ',
    firstNamePlaceholder: 'ชื่อ',
    lastNamePlaceholder: 'นามสกุล',
    savingButton: 'กำลังบันทึก',
    saveButton: 'บันทึก',
    editButton: 'แก้ไข',
    removeButton: 'นำออก',
    removingButton: 'กำลังนำออก',
    participantRole: 'ผู้เข้าร่วม',
    organizerRole: 'ผู้จัดกิจกรรม',
    modalActivityDescriptionLabel: 'รายละเอียดกิจกรรม',
    activityDescriptionModalTitle: 'รายละเอียดกิจกรรม',
    closeButtonAriaLabel: 'ปิด',
    loadFailedError: 'โหลดข้อมูลไม่สำเร็จ',
    accessDeniedError: 'คุณไม่มีสิทธิ์เข้าถึงกิจกรรมนี้ กำลังพากลับไปหน้ารายการกิจกรรม...',
    fillAllFieldsError: 'กรุณากรอกข้อมูลให้ครบ',
    saveFailedError: 'บันทึกข้อมูลไม่สำเร็จ',
    saveFailedFallbackError: 'ไม่สามารถบันทึกข้อมูลได้',
    removeParticipantConfirm: 'นำ {name} ({id}) ออกจากกิจกรรมนี้?\n\nข้อมูลนักศึกษาและกิจกรรมอื่นของนักศึกษาจะยังอยู่',
    removeFailedError: 'นำนักศึกษาออกไม่สำเร็จ'
  },

  studentNotifications: {
    title: 'การแจ้งเตือน',
    markAllRead: 'ทำเครื่องหมายว่าอ่านทั้งหมด',
    empty: 'ยังไม่มีการแจ้งเตือน',
    loadError: 'โหลดการแจ้งเตือนไม่สำเร็จ',
    justNow: 'เมื่อสักครู่',
    unread: 'ยังไม่ได้อ่าน',
    approved: "กิจกรรม '{title}' ของคุณได้รับการอนุมัติแล้ว ✓",
    rejected: "กิจกรรม '{title}' ของคุณถูกปฏิเสธ - {reason}",
    requestApproved: "คำขอ '{title}' ของคุณได้รับการอนุมัติแล้ว ✓",
    requestRejected: "คำขอ '{title}' ของคุณถูกปฏิเสธ - {reason}",
    loadMore: 'ดูเพิ่มเติม',
    loadingMore: 'กำลังโหลด...',
    clearAll: 'ลบทั้งหมด',
    cancel: 'ยกเลิก',
    confirmClear: 'ลบ',
    clearing: 'กำลังลบ...',
    clearFailed: 'ลบไม่สำเร็จ กรุณาลองอีกครั้ง',
    clearConfirm: 'ลบการแจ้งเตือนทั้งหมดใช่ไหม? ลบแล้วกู้คืนไม่ได้'
  },

  studentContact: {
    title: 'ติดต่อเรา',
    message: 'หากมีข้อสงสัยหรือต้องการความช่วยเหลือ กรุณาติดต่อเรา',
    channelsTitle: 'ช่องทางการติดต่อ',
    comingSoon: 'ข้อมูลการติดต่อจะเพิ่มเร็ว ๆ นี้'
  },

  studentLayout: {
    notifications: 'การแจ้งเตือน',
    unread: 'ยังไม่ได้อ่าน',
    markAllRead: 'อ่านทั้งหมดแล้ว',
    noNotifications: 'ไม่มีการแจ้งเตือน',
    toggleSidebar: 'ย่อ/ขยายแถบด้านข้าง',
    myProfile: 'โปรไฟล์ของฉัน',
    studentProfileAlt: 'รูปโปรไฟล์นักศึกษา',
    idLabel: 'รหัสนักศึกษา',
    faculty: 'คณะ',
    major: 'สาขาวิชา',
    email: 'อีเมล',
    cannotLoadNotifications: 'ไม่สามารถโหลดการแจ้งเตือนได้',
    logoutAndSwitchStudent: 'ออกจากระบบ / สลับนักศึกษา'
  },

  adminLogin: {
    title: 'เข้าสู่ระบบผู้ดูแลระบบ',
    subtitle: 'คณะวิทยาศาสตร์',
    signInButton: 'เข้าสู่ระบบ',
    loading: 'กำลังโหลด...',
    bypassNotice: 'โหมดทดสอบ: เลือกหรือพิมพ์อีเมลแอดมินทดสอบ ไม่ต้องใส่รหัสผ่าน',
    emailLabel: 'อีเมลแอดมิน',
    emailPlaceholder: 'เช่น central@test.local',
    accountsTitle: 'บัญชีแอดมินทดสอบ',
    centralMajor: 'แอดมินกลาง (ทุกสาขา)',
    unknownEmail: 'ไม่พบอีเมลนี้ในรายชื่อแอดมินทดสอบ',
    sessionExpired: 'กรุณาเลือกอีเมลแอดมินใหม่อีกครั้ง',
    backendUnavailable: 'เชื่อมต่อ backend ไม่ได้ ตรวจสอบว่า backend รันอยู่',
    retry: 'ลองอีกครั้ง',
    bypassDisabledTitle: 'โหมดทดสอบแอดมิน (bypass) ยังไม่ได้เปิด จึงเข้าหน้า admin ไม่ได้',
    bypassDisabledStep1: '1. เพิ่มบรรทัดนี้ในไฟล์ .env ที่ root ของโปรเจกต์',
    bypassDisabledStep2: '2. รีสตาร์ท backend แล้วกด "ลองอีกครั้ง"'
  },

  studentLogin: {
    loginTitle: 'เข้าสู่ระบบ',
    loginSubtitle: 'ใช้อีเมลและรหัสผ่านของคุณ สำหรับทั้งนักศึกษาและแอดมิน',
    languageLabel: 'ภาษา',
    sessionExpired: 'เซสชันหมดอายุหรือบัญชีถูกเปลี่ยนแปลง กรุณาเข้าสู่ระบบใหม่',
    universityName: 'มหาวิทยาลัยเชียงใหม่',
    facultyName: 'คณะวิทยาศาสตร์',
    adminLogin: 'เข้าสู่ระบบผู้ดูแล',
    emailLabel: 'อีเมล',
    emailPlaceholder: 'name@example.com',
    passwordLabel: 'รหัสผ่าน',
    showPassword: 'แสดงรหัสผ่าน',
    hidePassword: 'ซ่อนรหัสผ่าน',
    rememberMe: 'จดจำฉันไว้',
    forgotPassword: 'ลืมรหัสผ่าน?',
    signInButton: 'เข้าสู่ระบบ',
    newToPortal: 'เพิ่งเคยใช้งานระบบนี้?',
    contactItSupport: 'ติดต่อฝ่ายไอที',
    forAccess: 'เพื่อขอสิทธิ์เข้าใช้งาน',
    emailRequiredError: 'กรุณากรอกอีเมล',
    passwordRequiredError: 'กรุณากรอกรหัสผ่าน',
    invalidCredentialsError: 'อีเมลหรือรหัสผ่านไม่ถูกต้อง',
    emailNotFoundError: 'ไม่พบอีเมลนี้ในระบบ',
    wrongPasswordError: 'รหัสผ่านไม่ถูกต้อง',
    authUnavailableError: 'ระบบเข้าสู่ระบบยังไม่พร้อม กรุณาตรวจสอบการตั้งค่าระบบยืนยันตัวตนของ backend',
    backendUnavailableError: 'เชื่อมต่อ backend ไม่ได้ กรุณาลองใหม่'
  },

  skillLevelEditor: {
    notRelated: 'ไม่เกี่ยวข้อง',
    level: 'ระดับ',
    notApplicable: 'ไม่เกี่ยวข้อง'
  },

  adminNotifications: {
    title: 'การแจ้งเตือน',
    markAllRead: 'ทำเครื่องหมายว่าอ่านทั้งหมด',
    empty: 'ยังไม่มีการแจ้งเตือน',
    loadError: 'โหลดการแจ้งเตือนไม่สำเร็จ',
    justNow: 'เมื่อสักครู่',
    unread: 'ยังไม่ได้อ่าน',
    externalSubmitted: 'นักศึกษา {name} ส่งคำขอเพิ่มกิจกรรมภายนอก {title}',
    externalResubmitted: 'นักศึกษา {name} แก้ไขและส่งคำขอกิจกรรมภายนอก {title} อีกครั้ง',
    loadMore: 'ดูเพิ่มเติม',
    loadingMore: 'กำลังโหลด...',
    clearAll: 'ลบทั้งหมด',
    cancel: 'ยกเลิก',
    confirmClear: 'ลบ',
    clearing: 'กำลังลบ...',
    clearFailed: 'ลบไม่สำเร็จ กรุณาลองอีกครั้ง',
    clearConfirm: 'ลบการแจ้งเตือนทั้งหมดออกจากกระดิ่งของคุณใช่ไหม? แอดมินคนอื่นยังเห็นตามปกติ'
  },

  adminSettings: {
    title: 'ตั้งค่า',
    subtitle: 'จัดการการตั้งค่าระบบสำหรับแอดมินกลาง',
    subtitleBranch: 'จัดการนักศึกษาสาขา{major} และหัวเอกสารทรานสคริปต์',
    sectionStudentsDescriptionBranch: 'นำเข้าและจัดการข้อมูลนักศึกษาสาขา{major}',
    importBranchNote: 'นำเข้าได้เฉพาะนักศึกษาสาขา{major} แถวที่เว้นช่องสาขาไว้จะใส่สาขา{major}ให้อัตโนมัติ',
    deleteAllMessageBranch: 'นักศึกษาสาขา{major}ทั้งหมด {count} คนจะถูกลบ พร้อมการเข้าร่วมกิจกรรม กิจกรรมภายนอก ไฟล์หลักฐาน คำขอ และการแจ้งเตือนของทุกคน (นักศึกษาสาขาอื่นไม่ถูกลบ)',
    importTitle: 'นำเข้าข้อมูลนักศึกษา',
    importDescription: 'อัปโหลดไฟล์ Excel หรือ CSV เพื่อเพิ่มนักศึกษาใหม่เข้าระบบ รหัสนักศึกษาที่มีอยู่แล้วจะถูกข้าม',
    downloadTemplate: 'ดาวน์โหลด Template',
    templateError: 'ดาวน์โหลด Template ไม่สำเร็จ',
    requiredColumns: 'คอลัมน์ในไฟล์',
    dropzoneTitle: 'ลากไฟล์มาวางที่นี่ หรือคลิกเพื่อเลือกไฟล์',
    dropzoneHint: 'รองรับ .xlsx, .xls และ .csv ขนาดไม่เกิน 5MB',
    chooseFile: 'เลือกไฟล์',
    fileTypeError: 'รองรับเฉพาะไฟล์ .xlsx, .xls และ .csv เท่านั้น',
    fileSizeError: 'ไฟล์ใหญ่เกิน 5MB',
    reading: 'กำลังอ่านไฟล์...',
    requestError: 'ดำเนินการไม่สำเร็จ กรุณาลองใหม่',
    previewTitle: 'ตรวจสอบข้อมูลก่อนนำเข้า',
    previewHint: 'ตรวจสอบรายการด้านล่าง แล้วกด \'ยืนยันการนำเข้า\' เพื่อบันทึกเฉพาะรายการใหม่',
    columnRow: 'แถว',
    columnStudentId: 'รหัสนักศึกษา',
    columnFirstName: 'ชื่อ',
    columnLastName: 'นามสกุล',
    columnEmail: 'อีเมล',
    columnMajor: 'สาขาวิชา',
    columnStatus: 'สถานะ',
    statusNew: 'เพิ่มใหม่',
    statusDuplicate: 'ซ้ำ (ข้าม)',
    statusInvalid: 'ไม่ถูกต้อง',
    summaryTotal: 'ทั้งหมด',
    summaryNew: 'จะนำเข้า',
    summarySuccess: 'นำเข้าสำเร็จ',
    summarySkipped: 'ข้าม (ซ้ำ)',
    summaryFailed: 'ไม่ถูกต้อง',
    noNewRows: 'ไม่มีรายการใหม่ที่นำเข้าได้',
    emptyFile: 'ไม่พบข้อมูลนักศึกษาในไฟล์',
    confirmImport: 'ยืนยันการนำเข้า',
    importing: 'กำลังนำเข้า...',
    chooseAnotherFile: 'เลือกไฟล์ใหม่',
    resultTitle: 'นำเข้าข้อมูลเสร็จสิ้น',
    issuesTitle: 'รายการที่ไม่ได้นำเข้า',
    importAnother: 'นำเข้าไฟล์อื่น',
    studentsTitle: 'นักศึกษาทั้งหมด',
    studentsDescription: 'ดูและจัดการนักศึกษาทุกคนในระบบ',
    studentsDescriptionBranch: 'ดูและจัดการนักศึกษาสาขา{major}',
    studentsCount: 'ทั้งหมด {count} คน',
    studentsFound: 'พบ {count} จาก {all} คน',
    searchPlaceholder: 'ค้นหารหัส ชื่อ อีเมล หรือสาขา',
    deleteAllButton: 'ลบทั้งหมด',
    columnName: 'ชื่อ-นามสกุล',
    columnActivities: 'กิจกรรม',
    columnAdded: 'วันที่เพิ่ม',
    columnActions: 'จัดการ',
    activitySummary: 'คณะ {faculty} · ภายนอก {external}',
    noMajor: 'ไม่มีสาขา',
    noMajorHint: 'แอดมินสาขาจะไม่เห็นนักศึกษาคนนี้',
    deleteStudentAria: 'ลบ {name}',
    studentsLoading: 'กำลังโหลดรายชื่อนักศึกษา...',
    studentsLoadError: 'โหลดรายชื่อนักศึกษาไม่สำเร็จ',
    retry: 'ลองใหม่',
    studentsEmpty: 'ยังไม่มีนักศึกษาในระบบ',
    studentsNoMatch: 'ไม่พบนักศึกษาที่ตรงกับคำค้นหา',
    pageInfo: 'หน้า {page} จาก {pages}',
    previousPage: 'หน้าก่อนหน้า',
    nextPage: 'หน้าถัดไป',
    deleteOneTitle: 'ลบนักศึกษา',
    deleteOneMessage: 'ต้องการลบ \'{name}\' (รหัส {id}) ออกจากระบบใช่หรือไม่?',
    deleteRelatedWarning: 'ข้อมูลของนักศึกษาคนนี้จะถูกลบไปด้วย: การเข้าร่วมกิจกรรมคณะ {faculty} รายการ และกิจกรรมภายนอก {external} รายการ (รวมไฟล์หลักฐาน)',
    deleteAllTitle: 'ลบนักศึกษาทั้งหมด',
    deleteAllMessage: 'นักศึกษาทั้งหมด {count} คนจะถูกลบ พร้อมการเข้าร่วมกิจกรรม กิจกรรมภายนอก ไฟล์หลักฐาน คำขอ และการแจ้งเตือนของทุกคน',
    deleteAllKeepsActivities: 'กิจกรรมของคณะ (ที่แอดมินสร้าง) ยังอยู่',
    deleteAllConfirmLabel: 'พิมพ์ {word} เพื่อยืนยัน',
    deleteConfirmWord: 'DELETE',
    cannotUndo: 'การลบนี้ย้อนกลับไม่ได้',
    cancelButton: 'ยกเลิก',
    deleteButton: 'ลบ',
    deleting: 'กำลังลบ...',
    deleteFailed: 'ลบไม่สำเร็จ กรุณาลองใหม่',
    deletedOne: 'ลบ \'{name}\' เรียบร้อยแล้ว',
    deletedAll: 'ลบนักศึกษาทั้งหมด {count} คนเรียบร้อยแล้ว',
    sectionStudents: 'จัดการนักศึกษา',
    sectionAdmins: 'จัดการแอดมิน',
    adminsTitle: 'แอดมินสาขา',
    adminsDescription: 'แอดมินสาขาเห็นและจัดการได้เฉพาะข้อมูลของสาขาตัวเอง',
    adminsCount: 'ทั้งหมด {count} คน',
    addAdminButton: 'เพิ่มแอดมิน',
    columnBranch: 'สาขา',
    adminsLoading: 'กำลังโหลดรายชื่อแอดมิน...',
    adminsLoadError: 'โหลดรายชื่อแอดมินไม่สำเร็จ',
    adminsEmpty: 'ยังไม่มีแอดมินสาขา',
    deleteAdminAria: 'ลบแอดมิน {name}',
    addAdminTitle: 'เพิ่มแอดมิน',
    addAdminSubtitle: 'แอดมินสาขาที่เพิ่มจะเห็นเฉพาะข้อมูลของสาขาที่เลือก',
    fieldEmail: 'อีเมล',
    fieldBranch: 'สาขา',
    selectBranch: 'เลือกสาขา',
    adminRequiredError: 'กรุณากรอกอีเมลและเลือกสาขา',
    adminEmailError: 'รูปแบบอีเมลไม่ถูกต้อง',
    adminSaveFailed: 'เพิ่มแอดมินไม่สำเร็จ กรุณาลองใหม่',
    saveButton: 'บันทึก',
    saving: 'กำลังบันทึก...',
    adminCreated: 'เพิ่มแอดมิน \'{name}\' เรียบร้อยแล้ว',
    deleteAdminTitle: 'ลบแอดมินสาขา',
    deleteAdminMessage: 'ต้องการลบแอดมิน \'{name}\' ({email}) ใช่หรือไม่?',
    deleteAdminWarning: 'บัญชีนี้จะเข้าสู่ระบบไม่ได้อีก และถ้ากำลังใช้งานอยู่จะถูกออกจากระบบทันที',
    adminDeleted: 'ลบแอดมิน \'{name}\' เรียบร้อยแล้ว',
    viewAll: 'ดูทั้งหมด ({count} คน)',
    showLess: 'แสดงน้อยลง',
    defaultPasswordNote: 'แอดมินใหม่เข้าสู่ระบบที่หน้า /login ด้วยอีเมลนี้ รหัสผ่านเริ่มต้นคือ 1234',
    sectionStudentsDescription: 'นำเข้าและจัดการข้อมูลนักศึกษาในระบบ',
    sectionAdminsDescription: 'เพิ่มและลบแอดมินสาขา',
    sectionTranscript: 'จัดการทรานสคริปต์',
    sectionTranscriptDescription: 'แก้ไขหัวข้อและรูปแบบใบทรานสคริปต์',
    manageSection: 'จัดการ',
    closeSection: 'ปิด',
    transcriptHeaderTitle: 'หัวเอกสารทรานสคริปต์',
    transcriptHeaderDescription: 'ข้อความส่วนหัวและผู้ลงนามที่แสดงในใบทรานสคริปต์ PDF ทั้งแบบ A และ B',
    transcriptThai: 'ภาษาไทย',
    transcriptEnglish: 'English',
    transcriptUniversity: 'ชื่อมหาวิทยาลัย',
    transcriptFaculty: 'ชื่อคณะ',
    transcriptTitle: 'หัวข้อเอกสาร',
    transcriptSignerName: 'ชื่อผู้รับรอง',
    transcriptSignerPosition: 'ตำแหน่งผู้รับรอง',
    transcriptHint: 'มีผลกับใบทรานสคริปต์ที่สร้างหลังบันทึก ช่องที่เว้นว่างจะใช้ค่าเริ่มต้น (ข้อความสีจางในช่อง)',
    transcriptResetDefaults: 'ใช้ค่าเริ่มต้น',
    transcriptLoading: 'กำลังโหลดค่าตั้งทรานสคริปต์...',
    transcriptLoadError: 'โหลดค่าตั้งทรานสคริปต์ไม่สำเร็จ',
    transcriptSaveFailed: 'บันทึกไม่สำเร็จ กรุณาลองใหม่',
    transcriptPreviewTitle: 'ตัวอย่างทรานสคริปต์',
    transcriptPreviewDescription: 'แสดงด้วยข้อมูลนักศึกษาสมมติและค่าที่กรอกอยู่ (ยังไม่บันทึก) อัปเดตเองหลังหยุดพิมพ์',
    transcriptPreviewStyle: 'รูปแบบ',
    transcriptPreviewLanguage: 'ภาษา',
    transcriptStyleA: 'แบบ A คลาสสิก',
    transcriptStyleB: 'แบบ B ทันสมัย',
    transcriptPreviewRefresh: 'อัปเดตตัวอย่าง',
    transcriptPreviewLoading: 'กำลังสร้างตัวอย่าง...',
    transcriptPreviewFailed: 'สร้างตัวอย่างไม่สำเร็จ',
    transcriptSaved: 'บันทึกหัวเอกสารทรานสคริปต์แล้ว ใช้กับ PDF ที่สร้างต่อจากนี้'
  },

  studentTranscript: {
    title: 'ทรานสคริปต์กิจกรรม',
    subtitle: 'ดาวน์โหลดใบรับรองการเข้าร่วมกิจกรรม (PDF ขนาด A4)',
    loading: 'กำลังโหลด...',
    loadError: 'โหลดข้อมูลไม่สำเร็จ',
    retry: 'ลองอีกครั้ง',
    styleTitle: 'รูปแบบเอกสาร',
    styleA: 'แบบ A คลาสสิก',
    styleADescription: 'หัวกระดาษกลาง ฟอนต์มีหัว ตารางมีเส้นขอบ คะแนนทักษะเป็นช่องตัวเลข',
    styleB: 'แบบ B ทันสมัย',
    styleBDescription: 'แถบสีหัวกระดาษ คะแนนทักษะเป็นแถบ ตารางโล่ง มีช่อง QR',
    scopeTitle: 'ประเภทกิจกรรม',
    scopeAll: 'ทั้งหมด',
    scopeMajor: 'เฉพาะกิจกรรมของสาขาตัวเอง',
    scopeFaculty: 'เฉพาะกิจกรรมส่วนกลางของคณะ',
    scopeExternal: 'เฉพาะกิจกรรมภายนอก',
    activitiesUnit: 'กิจกรรม',
    yearTitle: 'ชั้นปี',
    currentYear: 'ชั้นปีปัจจุบัน: ปี',
    yearRule: 'เลือกได้ไม่เกินชั้นปีปัจจุบัน',
    yearUnknown: 'ไม่ทราบชั้นปีจากรหัสนักศึกษา จึงเลือกได้เฉพาะทุกชั้นปี',
    allYears: 'ทุกชั้นปี',
    yearPrefix: 'ปี',
    yearDisabled: 'เกินชั้นปีปัจจุบัน',
    demoNote: 'เอกสารเดโม มีลายน้ำ "ตัวอย่าง"',
    download: 'ดาวน์โหลด PDF',
    downloading: 'กำลังสร้าง PDF...',
    downloadError: 'ดาวน์โหลดไม่สำเร็จ',
    preview: 'ดูตัวอย่าง',
    previewTitle: 'ตัวอย่างทรานสคริปต์',
    previewLoading: 'กำลังสร้าง PDF...',
    close: 'ปิด',
    previewPopupBlocked: 'เบราว์เซอร์บล็อกการเปิดแท็บใหม่ กรุณาอนุญาต popup แล้วลองอีกครั้ง หรือกดดาวน์โหลด PDF',
    languageTitle: 'ภาษาของเอกสาร',
    languageHint: 'ข้อความทั้งฉบับเป็นภาษาที่เลือก ชื่อและชื่อกิจกรรมแสดงตามที่บันทึกไว้ในระบบ',
    languageThai: 'ภาษาไทย',
    languageThaiNote: 'วันที่และปีการศึกษาเป็น พ.ศ.',
    languageEnglish: 'English',
    languageEnglishNote: 'วันที่และปีการศึกษาเป็น ค.ศ.',
    previewThai: 'ดูตัวอย่าง (ภาษาไทย)',
    previewEnglish: 'ดูตัวอย่าง (English)',
    downloadThai: 'ดาวน์โหลด PDF (ภาษาไทย)',
    downloadEnglish: 'ดาวน์โหลด PDF (English)'
  },

  studentGuide: {
    title: 'คู่มือการใช้งาน',
    subtitle: 'วิธีใช้งานระบบติดตามกิจกรรมและทักษะสำหรับนักศึกษา เลือกหัวข้อด้านล่างเพื่อดูรายละเอียด',
    jumpTo: 'ไปที่หัวข้อ',
    expandAll: 'ขยายทั้งหมด',
    collapseAll: 'ย่อทั้งหมด',
    openPage: 'เปิดหน้า',
    tip: 'เคล็ดลับ',
    stillNeedHelp: 'ยังมีคำถาม? ติดต่อเจ้าหน้าที่ทางอีเมล',
    sections: {
      activities: {
        title: 'กิจกรรมของฉัน',
        summary: 'ดูกิจกรรมทั้งหมดที่คุณเข้าร่วม ทั้งกิจกรรมคณะและกิจกรรมภายนอก',
        topics: [
          {
            heading: 'กิจกรรมคณะคืออะไร',
            text: 'กิจกรรมที่คณะหรือสาขาของคุณจัด เมื่อแอดมินบันทึกชื่อคุณเป็นผู้เข้าร่วมหรือผู้จัด กิจกรรมจะขึ้นในหน้านี้เอง ไม่ต้องส่งคำขอ',
            tip: 'กิจกรรมที่สาขาอื่นในคณะเป็นผู้จัด จะแสดงในแท็บ "กิจกรรมภายนอก"'
          },
          {
            heading: 'กิจกรรมภายนอกคืออะไร',
            text: 'กิจกรรมที่จัดนอกคณะ เช่น ค่าย งานอบรม งานจิตอาสา หรือการแข่งขันของหน่วยงานอื่น คุณส่งข้อมูลและหลักฐานเองผ่านเมนู "เพิ่มกิจกรรมภายนอก" และกิจกรรมจะถูกนับเมื่อแอดมินสาขาของคุณอนุมัติแล้ว'
          },
          {
            heading: 'วิธีดูรายละเอียดกิจกรรม',
            steps: [
              'กดที่การ์ดกิจกรรม หรือกดปุ่ม "รายละเอียด"',
              'หน้าต่างรายละเอียดจะแสดงวันที่ สถานที่ ผู้จัด บทบาทของคุณ คำอธิบาย และทักษะพร้อมระดับ',
              'สำหรับกิจกรรมภายนอก กด "ดูหลักฐาน" เพื่อเปิดไฟล์ที่แนบไว้',
              'สถานะด้านล่างบอกว่ากิจกรรมอนุมัติแล้ว รอตรวจสอบ หรือไม่อนุมัติ (พร้อมเหตุผล)'
            ]
          },
          {
            heading: 'วิธีกรองและค้นหากิจกรรม',
            steps: [
              'เลือกแท็บ "ทั้งหมด" "กิจกรรมคณะ" "กิจกรรมภายนอก" หรือ "รายการที่ส่ง" (คำขอที่คุณส่งไปทุกสถานะ)',
              'พิมพ์ชื่อกิจกรรมในช่องค้นหาด้านบน',
              'กด "กรองตามวันที่" เพื่อดูเฉพาะวันที่ต้องการ กด "ล้างค่า" เพื่อยกเลิกตัวกรอง',
              'ถ้ากิจกรรมมีจำนวนมาก เลื่อนลงแล้วกด "โหลดกิจกรรมเพิ่มเติม"'
            ]
          }
        ]
      },
      external: {
        title: 'เพิ่มกิจกรรมภายนอก',
        summary: 'ส่งกิจกรรมที่เข้าร่วมนอกคณะ พร้อมหลักฐาน เพื่อให้แอดมินอนุมัติ',
        topics: [
          {
            heading: 'วิธีกรอกข้อมูลกิจกรรม',
            steps: [
              'กรอกชื่อกิจกรรมและหน่วยงาน/องค์กรที่จัด',
              'เลือกประเภทกิจกรรม ถ้าไม่มีประเภทที่ตรง ให้เลือก "อื่น ๆ" แล้วพิมพ์ระบุเอง',
              'เลือกวันที่เริ่มต้นและวันที่สิ้นสุด (วันสิ้นสุดต้องไม่อยู่ก่อนวันเริ่ม)',
              'ระบุสถานที่ หรือลิงก์ถ้าเป็นกิจกรรมออนไลน์',
              'เขียนรายละเอียดว่าคุณทำอะไรและได้เรียนรู้อะไรจากกิจกรรม'
            ],
            tip: 'ช่องที่มีเครื่องหมาย * ต้องกรอกให้ครบก่อนส่ง'
          },
          {
            heading: 'วิธีเลือกบทบาทและทักษะ',
            steps: [
              'เลือกบทบาท: Participant (ผู้เข้าร่วม) หรือ Staff (ผู้จัด / ทีมงาน)',
              'หลังเลือกบทบาท แผงทักษะจะแสดงขึ้น ชุดทักษะจะต่างกันตามบทบาท',
              'กด "ปรับระดับทักษะ" ทุกทักษะเริ่มที่ระดับ 3 ปรับเป็น 1–5 ตามที่คุณพัฒนาจริง',
              'ทักษะที่ไม่เกี่ยวกับกิจกรรม ให้ติ๊ก "ไม่เกี่ยวข้อง"',
              'ต้องมีอย่างน้อย 1 ทักษะ แล้วกด "บันทึก"'
            ]
          },
          {
            heading: 'วิธีแนบหลักฐาน',
            text: 'แนบเกียรติบัตร หรือรูปถ่ายขณะเข้าร่วมกิจกรรม อย่างน้อย 1 ไฟล์ และสูงสุด 10 ไฟล์ รองรับ JPG, PNG และ PDF ไฟล์ละไม่เกิน 5MB กด "คลิกเพื่อเลือกไฟล์" เพื่อแนบ และกดปุ่ม X ที่ไฟล์เพื่อเอาออก',
            tip: 'รูปที่เห็นชื่อกิจกรรม วันที่ หรือตัวคุณชัดเจน ช่วยให้แอดมินอนุมัติได้เร็วขึ้น'
          },
          {
            heading: 'ขั้นตอนการส่งและรอการอนุมัติ',
            steps: [
              'กด "ส่งเพื่อขออนุมัติ" แล้วกด "ยืนยัน" ในหน้าต่างที่ขึ้นมา',
              'คำขอจะอยู่ในแท็บ "รายการที่ส่ง" ของหน้ากิจกรรมของฉัน สถานะ "รอดำเนินการ"',
              'แอดมินของสาขาคุณจะตรวจสอบข้อมูล หลักฐาน และระดับทักษะ',
              'เมื่ออนุมัติแล้ว กิจกรรมจะแสดงในแท็บ "กิจกรรมภายนอก" และนับในหน้าทักษะของฉันกับทรานสคริปต์'
            ],
            tip: 'ระหว่างรอดำเนินการ คุณลบคำขอได้ถ้าส่งผิด (ไฟล์หลักฐานจะถูกลบด้วย)'
          },
          {
            heading: 'วิธีแก้ไขกิจกรรมที่ถูกปฏิเสธ',
            steps: [
              'ไปที่แท็บ "รายการที่ส่ง" กิจกรรมที่ไม่ผ่านจะมีสถานะ "ไม่อนุมัติ" พร้อมเหตุผลจากแอดมิน',
              'กดปุ่ม "แก้ไข" ฟอร์มจะเปิดขึ้นพร้อมข้อมูลและหลักฐานเดิม',
              'แก้ไขตามเหตุผลที่ได้รับ เพิ่มหรือลบไฟล์หลักฐานได้',
              'กด "ส่งใหม่เพื่อขออนุมัติ" สถานะจะกลับเป็น "รอดำเนินการ" อีกครั้ง'
            ]
          }
        ]
      },
      skills: {
        title: 'ทักษะของฉัน',
        summary: 'ดูภาพรวมทักษะที่ได้จากกิจกรรม และเปรียบเทียบกับค่าเฉลี่ย',
        topics: [
          {
            heading: 'วิธีอ่านกราฟเรดาร์ทักษะ',
            steps: [
              'แต่ละมุมของกราฟคือ 1 ทักษะ จุดยิ่งห่างจากจุดกลาง คะแนนยิ่งสูง (เต็ม 5)',
              'คะแนนคือค่าเฉลี่ยระดับทักษะจากกิจกรรมที่นับ',
              'เลือกปีและเทอม (ทั้งปี / เทอม 1 / เทอม 2) ที่มุมขวาบนเพื่อดูแต่ละช่วง',
              'เลือกชุด Skill: "Skill ผู้เข้าร่วม" คิดจากกิจกรรมที่คุณเข้าร่วม ส่วน "Skill ผู้จัด (Staff)" คิดจากกิจกรรมที่คุณเป็นผู้จัดเท่านั้น',
              'ตารางใต้กราฟแสดงกิจกรรมที่ใช้คำนวณคะแนน'
            ]
          },
          {
            heading: 'ความหมายของแต่ละทักษะ',
            groups: [
              {
                label: 'Skill ผู้เข้าร่วม (Participant)',
                items: [
                  { term: 'Arts, Culture, and Traditions', text: 'ศิลปะ วัฒนธรรม และประเพณี' },
                  { term: 'Volunteerism', text: 'จิตอาสาและการมีส่วนร่วมเพื่อสังคม' },
                  { term: 'Academics', text: 'การเรียนรู้และพัฒนาทางวิชาการ' },
                  { term: 'Internationalization', text: 'ความเป็นสากลและการเรียนรู้ข้ามวัฒนธรรม' },
                  { term: 'Health Promotion', text: 'การส่งเสริมสุขภาพและความเป็นอยู่ที่ดี' },
                  { term: 'Nature and Environmental Conservation', text: 'การอนุรักษ์ธรรมชาติและสิ่งแวดล้อม' }
                ]
              },
              {
                label: 'Skill ผู้จัด (Staff)',
                items: [
                  { term: 'Creative Leadership', text: 'ภาวะผู้นำเชิงสร้างสรรค์' },
                  { term: 'Innovation', text: 'การคิดและสร้างนวัตกรรม' },
                  { term: 'Entrepreneurship', text: 'ความเป็นผู้ประกอบการ' },
                  { term: 'Promote Equality', text: 'การส่งเสริมความเท่าเทียม' },
                  { term: 'Academic', text: 'ทักษะทางวิชาการ' },
                  { term: 'Nature and Environmental', text: 'ธรรมชาติและสิ่งแวดล้อม' }
                ]
              }
            ]
          },
          {
            heading: 'วิธีเปรียบเทียบกับค่าเฉลี่ยคณะ',
            steps: [
              'ที่ตัวเลือก "เปรียบเทียบกับ" เลือก "กิจกรรมคณะ" เพื่อเทียบกับค่าเฉลี่ยของนักศึกษาทั้งคณะ หรือ "กิจกรรมสาขา" เพื่อเทียบกับนักศึกษาในสาขาเดียวกัน',
              'กราฟจะแสดง 2 เส้น: ทักษะของคุณ และค่าเฉลี่ย ดูสีจากคำอธิบายใต้กราฟ',
              'มุมที่เส้นของคุณอยู่ด้านในค่าเฉลี่ย คือทักษะที่ควรหากิจกรรมเพิ่ม',
              'ตัวเลือก "กิจกรรมภายนอก" แสดงทักษะจากกิจกรรมภายนอกของคุณอย่างเดียว ไม่มีค่าเฉลี่ยให้เทียบ'
            ],
            tip: 'การเปรียบเทียบกับสาขาและคณะไม่นับกิจกรรมภายนอก เพื่อให้ทุกคนเทียบจากกิจกรรมชุดเดียวกัน'
          }
        ]
      },
      transcript: {
        title: 'ทรานสคริปต์',
        summary: 'สร้างใบรับรองการเข้าร่วมกิจกรรมเป็นไฟล์ PDF ขนาด A4',
        topics: [
          {
            heading: 'วิธีเลือกรูปแบบทรานสคริปต์',
            groups: [
              {
                label: 'รูปแบบเอกสาร',
                items: [
                  { term: 'แบบ A คลาสสิก', text: 'หัวกระดาษกลาง ตารางมีเส้นขอบ คะแนนทักษะเป็นช่องตัวเลข เหมาะกับเอกสารทางการ' },
                  { term: 'แบบ B ทันสมัย', text: 'แถบสีหัวกระดาษ คะแนนทักษะเป็นแถบ ตารางโล่ง อ่านง่าย' }
                ]
              },
              {
                label: 'ประเภทกิจกรรม',
                items: [
                  { term: 'ทั้งหมด', text: 'รวมทุกกิจกรรมที่นับได้' },
                  { term: 'เฉพาะสาขา / คณะ / ภายนอก', text: 'เลือกเฉพาะกลุ่มที่ต้องการ ตัวเลขข้างตัวเลือกคือจำนวนกิจกรรม' }
                ]
              }
            ]
          },
          {
            heading: 'วิธีดูตัวอย่างและดาวน์โหลด PDF',
            steps: [
              'เลือกรูปแบบ ประเภทกิจกรรม และภาษาของเอกสาร',
              'กด "ดูตัวอย่าง" เพื่อเปิด PDF บนหน้าจอ (บางอุปกรณ์จะเปิดในแท็บใหม่ ถ้าเบราว์เซอร์บล็อก popup ให้กดอนุญาต)',
              'ตรวจสอบข้อมูล ถ้าถูกต้องกด "ดาวน์โหลด PDF" เพื่อบันทึกไฟล์'
            ],
            tip: 'ทรานสคริปต์นับเฉพาะกิจกรรมคณะที่ไม่ถูกยกเลิก และกิจกรรมภายนอกที่อนุมัติแล้ว'
          },
          {
            heading: 'ความแตกต่างระหว่างฉบับภาษาไทยและภาษาอังกฤษ',
            groups: [
              {
                label: '',
                items: [
                  { term: 'ภาษาไทย', text: 'ข้อความทั้งฉบับเป็นภาษาไทย วันที่และปีการศึกษาเป็น พ.ศ.' },
                  { term: 'English', text: 'ข้อความทั้งฉบับเป็นภาษาอังกฤษ ชื่อสาขา ประเภทกิจกรรม และทักษะแปลเป็นอังกฤษ วันที่และปีการศึกษาเป็น ค.ศ. เหมาะกับยื่นสมัครงานหรือทุนต่างประเทศ' }
                ]
              }
            ],
            tip: 'ทั้งสองภาษา ชื่อของคุณและชื่อกิจกรรมแสดงตามที่บันทึกไว้ในระบบ (ไม่ได้แปลอัตโนมัติ)'
          }
        ]
      }
    }
  },
  adminGuide: {
    title: 'คู่มือการใช้งาน',
    subtitle: 'วิธีใช้งานระบบจัดการกิจกรรมและทักษะนักศึกษาสำหรับผู้ดูแล เลือกหัวข้อด้านล่างเพื่อดูรายละเอียด',
    guideFor: 'คู่มือสำหรับ:',
    roleCentral: 'แอดมินกลาง',
    roleBranch: 'แอดมินสาขา {major}',
    centralOnlyBadge: 'เฉพาะแอดมินกลาง',
    jumpTo: 'ไปที่หัวข้อ',
    expandAll: 'ขยายทั้งหมด',
    collapseAll: 'ย่อทั้งหมด',
    openPage: 'เปิดหน้า',
    tip: 'เคล็ดลับ',
    sections: {
      dashboard: {
        title: 'แดชบอร์ด',
        summary: 'ภาพรวมจำนวนกิจกรรม ผู้เข้าร่วม และทักษะ',
        topics: [
          {
            heading: 'วิธีอ่านสถิติภาพรวม',
            groups: [
              {
                label: '',
                items: [
                  { term: 'กิจกรรม', text: 'จำนวนกิจกรรมของคณะในช่วงที่เลือก ไม่นับกิจกรรมที่ยกเลิกและกิจกรรมภายนอกของนักศึกษา' },
                  { term: 'นักศึกษา', text: 'จำนวนนักศึกษาทั้งหมดในระบบ (ในขอบเขตที่คุณดูได้) ไม่ขึ้นกับช่วงเวลา' },
                  { term: 'ผู้เข้าร่วม', text: 'จำนวนนักศึกษา (ไม่นับซ้ำ) ที่เป็นผู้เข้าร่วมกิจกรรมในช่วงที่เลือก' },
                  { term: 'อัตราการสำเร็จ', text: 'กิจกรรมที่เสร็จสิ้นแล้ว ÷ กิจกรรมที่ไม่ถูกยกเลิก × 100 (กิจกรรมที่เลยวันสิ้นสุดแล้วนับว่าเสร็จสิ้น)' }
                ]
              }
            ]
          },
          {
            heading: 'วิธีใช้ตัวกรองปีและภาคเรียน',
            steps: [
              'ที่ส่วน "ประวัติแดชบอร์ด" เลือกปี (นับตามปีของวันที่เริ่มกิจกรรม)',
              'เลือกภาคเรียน: ทุกภาคเรียน, ภาคเรียนที่ 1 (ม.ค.–มิ.ย.) หรือภาคเรียนที่ 2 (ก.ค.–ธ.ค.)',
              'การ์ดสถิติ กราฟการเติบโต และการกระจายทักษะจะเปลี่ยนตามช่วงที่เลือกทันที'
            ]
          },
          {
            heading: 'วิธีใช้ตัวกรองสาขา',
            audience: 'central',
            steps: [
              'เลือกสาขาจากรายการ "สาขา" เพื่อดูเฉพาะข้อมูลของสาขานั้น หรือเลือก "ทุกสาขา" เพื่อดูภาพรวมทั้งคณะ',
              'ตัวกรองสาขาแบบเดียวกันมีในหน้ากิจกรรม ทักษะนักศึกษา และการอนุมัติ'
            ]
          },
          {
            heading: 'ข้อมูลที่คุณเห็น',
            audience: 'branch',
            text: 'แดชบอร์ดแสดงเฉพาะข้อมูลของสาขาคุณโดยอัตโนมัติ ทั้งกิจกรรมที่สาขาจัดและนักศึกษาในสาขา กิจกรรมส่วนกลางที่แอดมินกลางสร้างจะไม่ถูกนับในตัวเลขของแดชบอร์ด'
          },
          {
            heading: 'วิธีอ่านกราฟการเติบโตของกิจกรรม',
            steps: [
              'แต่ละแท่งคือจำนวนกิจกรรมที่เริ่มในเดือนนั้น (ไม่นับกิจกรรมที่ยกเลิก)',
              'สลับ "รายเดือน" / "รายไตรมาส" เพื่อเปลี่ยนการจัดกลุ่ม',
              'คลิกชื่อเดือนหรือไตรมาสใต้กราฟ เพื่อให้การ์ดสถิติและการกระจายทักษะแสดงเฉพาะช่วงนั้น'
            ]
          },
          {
            heading: 'วิธีอ่านการกระจายทักษะของนักศึกษา',
            steps: [
              'สลับ "ผู้เข้าร่วม" / "บุคลากร" เพื่อดูทักษะชุดผู้เข้าร่วมหรือชุดผู้จัด',
              'แต่ละแถบคือค่าเฉลี่ยระดับทักษะที่ตั้งไว้ในกิจกรรม คิดเป็นเปอร์เซ็นต์ของระดับ 5 ตัวเลขในวงเล็บคือจำนวนกิจกรรมที่มีทักษะนั้น',
              'วงกลม "คะแนนเฉลี่ย" คือค่าเฉลี่ยของทุกทักษะที่มีข้อมูล',
              'ใช้ดูว่ากิจกรรมในช่วงนี้เน้นทักษะไหน และทักษะไหนยังมีกิจกรรมน้อย'
            ]
          }
        ]
      },
      activities: {
        title: 'กิจกรรม',
        summary: 'สร้างกิจกรรม จัดการผู้เข้าร่วม แก้ไขและยกเลิกกิจกรรม',
        topics: [
          {
            heading: 'วิธีสร้างกิจกรรมใหม่',
            steps: [
              'กด "สร้างกิจกรรมใหม่" ที่มุมขวาบนของหน้ากิจกรรม',
              'ขั้นที่ 1: กรอกประเภทกิจกรรม ชื่อกิจกรรม วันที่เริ่มต้น–สิ้นสุด ผู้รับผิดชอบหลัก และสถานที่ (ช่องที่มี * ต้องกรอก) ถ้าเลือกประเภท "อื่นๆ" ให้พิมพ์ระบุเอง แล้วกด "ถัดไป"',
              'ขั้นที่ 2: ตั้งระดับทักษะทั้งแท็บ "ผู้จัดกิจกรรม" และ "ผู้เข้าร่วม" ทุกทักษะเริ่มที่ระดับ 3 ปรับได้ 1–5 ทักษะที่ไม่เกี่ยวข้องให้ติ๊ก "ไม่เกี่ยวข้อง"',
              'กด "สร้างกิจกรรม"'
            ],
            tip: 'กิจกรรมที่แอดมินสาขาสร้างจะเป็นของสาขานั้น ส่วนกิจกรรมที่แอดมินกลางสร้างเป็นกิจกรรมส่วนกลางที่ทุกสาขาเห็น'
          },
          {
            heading: 'วิธีเพิ่มนักศึกษาเข้ากิจกรรม',
            steps: [
              'ในตาราง คอลัมน์ "จัดการผู้เข้าร่วม" กด "จัดการ" ของกิจกรรมที่ต้องการ',
              'เพิ่มทีละคน: เลือก "เพิ่มนักศึกษา" ค้นหาด้วยรหัสหรือชื่อ เลือกบทบาท "ผู้เข้าร่วม" หรือ "ผู้จัด" แล้วบันทึก',
              'เพิ่มหลายคน: เลือก "นำเข้าจากไฟล์" แล้วเลือกไฟล์ .xlsx, .xls หรือ .csv',
              'กด "ดูตัวอย่างก่อนนำเข้า" ตรวจตาราง (แก้ไขในตารางได้) แถวที่มีปัญหาจะถูกข้าม',
              'กด "ยืนยัน Import"'
            ],
            tip: 'นักศึกษาต้องมีข้อมูลในระบบก่อน (แอดมินกลางนำเข้าที่หน้าตั้งค่า) ถ้าไม่พบรหัสจะเพิ่มไม่ได้'
          },
          {
            heading: 'วิธีดาวน์โหลด Template สำหรับนำเข้า',
            text: 'ในหน้าต่าง "นำเข้าจากไฟล์" กด "ดาวน์โหลด Template" จะได้ไฟล์ Excel ที่มีคอลัมน์ รหัสนักศึกษา, ชื่อ, นามสกุล, อีเมล, สาขาวิชา พร้อมตัวอย่าง 2 แถว ลบแถวตัวอย่างแล้วกรอกข้อมูลจริง ถ้าต้องการกำหนดบทบาท เพิ่มคอลัมน์ Role (participant / organizer) ได้ ถ้าไม่ใส่จะเป็นผู้เข้าร่วม'
          },
          {
            heading: 'วิธีจัดการผู้เข้าร่วม (แก้ไข, นำออก)',
            steps: [
              'กด "ดูรายละเอียด" ของกิจกรรม เพื่อเปิดหน้ารายชื่อผู้เข้าร่วม',
              'กด "แก้ไข" ที่แถวของนักศึกษา เพื่อแก้ชื่อ นามสกุล คณะ สาขา หรือบทบาท (แก้รหัสนักศึกษาไม่ได้) แล้วกด "บันทึก"',
              'กด "นำออก" แล้วยืนยัน เพื่อเอานักศึกษาออกจากกิจกรรมนี้ (ข้อมูลนักศึกษาในระบบยังอยู่)'
            ]
          },
          {
            heading: 'วิธีแก้ไขและยกเลิกกิจกรรม',
            steps: [
              'ในตาราง คอลัมน์ "จัดการกิจกรรม" กด "จัดการ"',
              '"แก้ไขกิจกรรม": แก้ข้อมูล สถานะ และระดับทักษะ แล้วกด "บันทึกการเปลี่ยนแปลง"',
              '"ทำเครื่องหมายว่าเสร็จสิ้น" เมื่อจบกิจกรรม (กด "เปิดกิจกรรมอีกครั้ง" เพื่อย้อนกลับ)',
              '"ยกเลิกกิจกรรม": มีผลทันทีโดยไม่ถามยืนยัน กิจกรรมที่ยกเลิกจะไม่ถูกนับในทักษะและทรานสคริปต์ของนักศึกษา',
              '"ลบกิจกรรม": ระบบจะถามยืนยันก่อน และลบถาวร'
            ],
            tip: 'ถ้ากดยกเลิกผิด เปลี่ยนสถานะกลับได้ที่ "แก้ไขกิจกรรม" ถ้าต้องการเก็บประวัติไว้ ให้ใช้ยกเลิกแทนการลบ'
          },
          {
            heading: 'วิธีค้นหาและเรียงลำดับกิจกรรม',
            steps: [
              'พิมพ์ชื่อกิจกรรมในช่อง "ค้นหากิจกรรม" หรือช่องค้นหาด่วนเหนือตาราง (ค้นได้ทั้งชื่อกิจกรรมและผู้จัด)',
              'เลือก "หมวดหมู่" หรือ "ตั้งแต่วันที่" เพื่อกรอง',
              'เปลี่ยนการเรียงเป็น "เรียงตามรายการล่าสุด" หรือ "เรียงตามวันที่เริ่ม" และกดลูกศรเพื่อสลับเก่า–ใหม่'
            ]
          },
          {
            heading: 'วิธีใช้ตัวกรองสาขาในหน้ากิจกรรม',
            audience: 'central',
            text: 'เลือกสาขาจากรายการ "สาขา" เพื่อดูกิจกรรมของสาขานั้น (กิจกรรมส่วนกลางของคณะจะแสดงด้วยเสมอ) หรือเลือก "ทุกสาขา" เพื่อดูทั้งหมด'
          }
        ]
      },
      skills: {
        title: 'ทักษะนักศึกษา',
        summary: 'ภาพรวมทักษะ ทักษะรายบุคคล และเทียบกับระดับมาตรฐาน',
        topics: [
          {
            heading: 'วิธีดูภาพรวมทักษะของนักศึกษา',
            steps: [
              'การ์ด "คะแนนทักษะเฉลี่ย" และ "นักศึกษาที่ประเมินแล้ว" ด้านบนสรุปภาพรวม',
              'ใช้ตัวกรอง "ชุด Skill" (ผู้เข้าร่วม / ผู้จัด), "ชั้นปี" และ "สาขาวิชา" เพื่อดูเฉพาะกลุ่ม กด "ล้างตัวกรอง" เพื่อกลับไปดูทั้งหมด',
              'ส่วน "ทักษะเด่น" และ "ทักษะที่ควรพัฒนา" บอกทักษะที่สูงสุดและต่ำสุด พร้อมแนวทางพัฒนา'
            ],
            tip: 'คะแนนทักษะคิดจากกิจกรรมคณะและกิจกรรมภายนอกที่อนุมัติแล้ว'
          },
          {
            heading: 'วิธีดูทักษะรายบุคคล',
            steps: [
              'เลื่อนไปที่ตาราง "ทักษะรายบุคคล" ค้นหาด้วยรหัสหรือชื่อนักศึกษา',
              'กด "กรองนักศึกษา" เพื่อกรองตามทักษะเด่นหรือช่วงคะแนน',
              'กด "ดูเรดาร์" เพื่อเปิดการวิเคราะห์ระดับทักษะของนักศึกษาคนนั้น',
              'ในหน้าต่างนี้เลือก "เทียบกับ" สาขา / คณะ / ภายนอก เพื่อเทียบกับค่าเฉลี่ยของกลุ่ม และดูการวิเคราะห์ช่องว่างทักษะพร้อมคำแนะนำ'
            ]
          },
          {
            heading: 'วิธีดูประวัติกิจกรรมของนักศึกษา',
            text: 'ในตาราง "ทักษะรายบุคคล" กด "ดูกิจกรรม" จะเห็นรายการกิจกรรมทั้งหมดของนักศึกษา พร้อมประเภท (กิจกรรมของคณะ / กิจกรรมภายนอก) วันที่ บทบาท และสถานะ'
          },
          {
            heading: 'วิธีอ่านกราฟเรดาร์และระดับมาตรฐาน',
            steps: [
              'เลือกปีและช่วง (ทั้งปี / ภาคการศึกษาที่ 1 / ภาคการศึกษาที่ 2) ที่หัวกราฟ',
              'เลือก "มุมมอง": ภาพรวม, แยกชั้นปี, แยกสาขา หรือแยกสาขา × ชั้นปี (ซ้อนกันได้สูงสุด 3 กลุ่ม)',
              'เส้น "ระดับทักษะจริง" คือคะแนนเฉลี่ยของนักศึกษา เส้น "ระดับมาตรฐาน" คือเป้าหมายของคณะ (ค่าเริ่มต้น 4.0)',
              'ทักษะที่เส้นจริงอยู่ด้านในเส้นมาตรฐาน คือทักษะที่ควรจัดกิจกรรมเพิ่ม กด "ดูตัวเลขของแต่ละกลุ่ม" เพื่อดูค่าเป็นตัวเลข'
            ]
          },
          {
            heading: 'วิธีตั้งค่าระดับมาตรฐาน',
            audience: 'central',
            steps: [
              'กดปุ่ม "มาตรฐาน" ที่กราฟเรดาร์',
              'กำหนดค่า 1.0–5.0 ของแต่ละทักษะ (ตั้งแยกกันระหว่างชุดผู้เข้าร่วมและชุดผู้จัด)',
              'กด "บันทึกมาตรฐาน" ค่าที่ตั้งใช้กับทุกสาขาในคณะ'
            ]
          },
          {
            heading: 'วิธีใช้ตัวกรองสาขา',
            audience: 'central',
            text: 'เลือกสาขาจากรายการ "สาขา" ด้านบน เพื่อดูการ์ด กราฟ และตารางทักษะเฉพาะนักศึกษาในสาขานั้น'
          }
        ]
      },
      approvals: {
        title: 'การอนุมัติ',
        summary: 'ตรวจสอบและอนุมัติกิจกรรมภายนอกที่นักศึกษาส่งมา',
        topics: [
          {
            heading: 'วิธีดูรายการคำขอที่รอดำเนินการ',
            steps: [
              'การ์ดด้านบนแสดงจำนวนรอดำเนินการทั้งหมด อนุมัติวันนี้ และไม่อนุมัติวันนี้',
              'แท็บ "รอดำเนินการ" แสดงคำขอที่ยังไม่ได้ตรวจ',
              'กด "ตัวกรอง" เพื่อเลือกประเภท (การรับรองทักษะ / คำขอพิเศษ / กิจกรรมภายนอก) และ "เรียงลำดับ" เพื่อสลับใหม่–เก่า'
            ]
          },
          {
            heading: 'วิธีดูรายละเอียดของคำขอ',
            steps: [
              'กด "ดูรายละเอียด" ที่คำขอ',
              'ตรวจข้อมูลนักศึกษา ชื่อกิจกรรม ผู้จัด ประเภท บทบาท วันที่ และสถานที่',
              'ดู "หลักฐาน" (กดที่รูปหรือไฟล์เพื่อเปิดดู) และ "Skill Mapping (โดยนักศึกษา)" ระดับทักษะที่นักศึกษาประเมินตัวเอง'
            ]
          },
          {
            heading: 'วิธีอนุมัติกิจกรรมภายนอก',
            steps: [
              'กด "อนุมัติ" ระบบจะแสดงหน้าต่าง "ยืนยันการอนุมัติ" พร้อมระดับทักษะที่นักศึกษาประเมิน',
              'กด "ยืนยันอนุมัติ" แล้วกด "ตกลง" ที่หน้าต่างอนุมัติสำเร็จ',
              'กิจกรรมจะถูกนับในหน้าทักษะและทรานสคริปต์ของนักศึกษาทันที'
            ],
            tip: 'แอดมินแก้ระดับทักษะเองไม่ได้ ถ้าระดับไม่เหมาะสม ให้ไม่อนุมัติพร้อมเหตุผล นักศึกษาจะแก้แล้วส่งใหม่ได้'
          },
          {
            heading: 'วิธีไม่อนุมัติพร้อมระบุเหตุผล',
            steps: [
              'กด "ไม่อนุมัติ"',
              'พิมพ์เหตุผลในช่อง "ความคิดเห็น / เหตุผลที่ไม่อนุมัติ" (ต้องกรอก)',
              'กด "ยืนยันไม่อนุมัติ" นักศึกษาจะได้รับการแจ้งเตือนพร้อมเหตุผล'
            ],
            tip: 'เขียนให้ชัดว่าต้องแก้อะไร เช่น "หลักฐานไม่เห็นชื่อกิจกรรม กรุณาแนบเกียรติบัตร"'
          },
          {
            heading: 'วิธีดูรายการที่ไม่อนุมัติแล้ว',
            text: 'เปิดแท็บ "ถูกปฏิเสธ" เพื่อดูคำขอที่ไม่อนุมัติและเหตุผล เมื่อนักศึกษาแก้ไขแล้วส่งใหม่ คำขอจะกลับมาที่แท็บ "รอดำเนินการ" และคุณจะได้รับการแจ้งเตือน (รายการที่อนุมัติแล้วไม่แสดงในหน้านี้)'
          },
          {
            heading: 'วิธีใช้ตัวกรองสาขา',
            audience: 'central',
            text: 'เลือกสาขาจากรายการ "สาขา" เพื่อดูเฉพาะคำขอของนักศึกษาในสาขานั้น คำขอของนักศึกษาที่ยังไม่มีสาขาจะเห็นได้เฉพาะแอดมินกลาง'
          }
        ]
      },
      settings: {
        title: 'การตั้งค่า',
        summary: 'จัดการนักศึกษา แอดมินสาขา (แอดมินกลาง) และหัวเอกสารทรานสคริปต์',
        topics: [
          {
            heading: 'ขอบเขตของแอดมินสาขาในหน้าตั้งค่า',
            audience: 'branch',
            text: 'คุณนำเข้า ดู และลบได้เฉพาะนักศึกษาในสาขาของคุณ (แถวในไฟล์ที่เว้นช่องสาขาไว้จะใส่สาขาของคุณให้อัตโนมัติ ส่วนแถวที่เป็นสาขาอื่นจะไม่ถูกนำเข้า) หัวเอกสารทรานสคริปต์แก้ได้เหมือนแอดมินกลาง และมีผลกับทุกสาขา การเพิ่มหรือลบแอดมินทำได้เฉพาะแอดมินกลาง'
          },
          {
            heading: 'วิธีนำเข้านักศึกษาเข้าระบบ',
            steps: [
              'ที่หัวข้อ "จัดการนักศึกษา" กด "จัดการ"',
              'กด "เลือกไฟล์" รองรับ .xlsx, .xls และ .csv ขนาดไม่เกิน 5MB (CSV ใช้ได้ทั้ง UTF-8 และ Windows-874)',
              'ตรวจตารางก่อนนำเข้า: "เพิ่มใหม่" จะถูกนำเข้า "ซ้ำ (ข้าม)" คือรหัสที่มีอยู่แล้ว "ไม่ถูกต้อง" คือแถวที่ข้อมูลผิด',
              'กด "ยืนยันการนำเข้า" แล้วดูสรุปผลและรายการที่ไม่ได้นำเข้า'
            ],
            tip: 'ใส่สาขาวิชาให้ครบ นักศึกษาที่ไม่มีสาขา แอดมินสาขาจะไม่เห็น'
          },
          {
            heading: 'วิธีดาวน์โหลด Template Excel',
            text: 'ในส่วนนำเข้าข้อมูลนักศึกษา กด "ดาวน์โหลด Template" จะได้ไฟล์ Excel ที่มีหัวคอลัมน์ รหัสนักศึกษา, ชื่อ, นามสกุล, อีเมล, สาขาวิชา ทุกช่องตั้งเป็นข้อความไว้แล้ว รหัสนักศึกษาจึงไม่ถูกตัดเลขศูนย์'
          },
          {
            heading: 'วิธีดูและลบข้อมูลนักศึกษา',
            steps: [
              'ส่วน "นักศึกษาทั้งหมด" แสดง 5 คนล่าสุด กด "ดูทั้งหมด" เพื่อดูทุกคนและค้นหาด้วยรหัส ชื่อ อีเมล หรือสาขา',
              'กดไอคอนถังขยะที่แถว เพื่อลบนักศึกษาคนนั้น (การเป็นสมาชิกกิจกรรม กิจกรรมภายนอก และไฟล์หลักฐานจะถูกลบด้วย)',
              'กด "ลบทั้งหมด" แล้วพิมพ์ DELETE เพื่อยืนยันการลบนักศึกษาทุกคน (กิจกรรมของคณะยังอยู่)'
            ],
            tip: 'การลบย้อนกลับไม่ได้ ตรวจสอบให้แน่ใจก่อนยืนยัน'
          },
          {
            heading: 'วิธีเพิ่มแอดมินสาขาใหม่',
            audience: 'central',
            steps: [
              'ที่หัวข้อ "จัดการแอดมิน" กด "จัดการ" แล้วกด "เพิ่มแอดมิน"',
              'กรอกอีเมล และเลือกสาขา แล้วกด "บันทึก"',
              'แอดมินใหม่เข้าสู่ระบบที่หน้า login ด้วยอีเมลนั้นและรหัสผ่านเริ่มต้น 1234'
            ],
            tip: 'อีเมลต้องไม่ซ้ำกับแอดมินหรือนักศึกษาที่มีอยู่แล้ว'
          },
          {
            heading: 'วิธีลบแอดมินสาขา',
            audience: 'central',
            text: 'ในตารางแอดมินสาขา กดไอคอนถังขยะแล้วยืนยัน บัญชีนั้นจะถูกออกจากระบบทันที คุณลบบัญชีตัวเองหรือแอดมินกลางไม่ได้'
          },
          {
            heading: 'วิธีแก้ไขหัวเอกสารทรานสคริปต์',
            steps: [
              'ที่หัวข้อ "จัดการทรานสคริปต์" กด "จัดการ"',
              'แก้ชื่อมหาวิทยาลัย ชื่อคณะ หัวข้อเอกสาร ชื่อผู้รับรอง และตำแหน่งผู้รับรอง ทั้งภาษาไทยและอังกฤษ ช่องที่เว้นว่างจะใช้ค่าเริ่มต้น',
              'ดู "ตัวอย่างทรานสคริปต์" ด้านล่าง เลือกแบบ A / B และภาษาได้ ตัวอย่างอัปเดตเองหลังหยุดพิมพ์',
              'กด "บันทึก" ค่าใหม่ใช้กับ PDF ทุกใบที่นักศึกษาสร้างหลังจากนี้ กด "ใช้ค่าเริ่มต้น" เพื่อย้อนกลับ'
            ]
          }
        ]
      },
      notifications: {
        title: 'การแจ้งเตือน',
        summary: 'รับรู้เมื่อมีนักศึกษาส่งคำขอกิจกรรมภายนอก',
        topics: [
          {
            heading: 'วิธีดูการแจ้งเตือนจากกระดิ่ง',
            steps: [
              'ไอคอนกระดิ่งอยู่มุมขวาบนของทุกหน้า ตัวเลขสีแดงคือจำนวนที่ยังไม่ได้อ่าน',
              'กดกระดิ่งเพื่อเปิดรายการแจ้งเตือนล่าสุด 30 รายการ (รายการที่ยังไม่อ่านมีจุดสีฟ้า)',
              'กดที่รายการ ระบบจะเปิดหน้าการอนุมัติพร้อมรายละเอียดคำขอนั้นให้ทันที',
              'กด "ทำเครื่องหมายว่าอ่านทั้งหมด" เพื่อล้างตัวเลข'
            ],
            tip: 'ระบบตรวจการแจ้งเตือนใหม่ทุก 30 วินาที สถานะอ่านแล้วแยกตามบัญชีแอดมินแต่ละคน'
          },
          {
            heading: 'ประเภทการแจ้งเตือนที่จะได้รับ',
            groups: [
              {
                label: '',
                items: [
                  { term: 'ส่งคำขอกิจกรรมภายนอกใหม่', text: 'นักศึกษาส่งกิจกรรมภายนอกเข้ามาให้ตรวจ (ไอคอนสีฟ้า)' },
                  { term: 'แก้ไขและส่งคำขออีกครั้ง', text: 'นักศึกษาแก้ไขกิจกรรมที่ถูกไม่อนุมัติแล้วส่งกลับมาใหม่ (ไอคอนสีส้ม)' }
                ]
              }
            ]
          },
          {
            heading: 'แอดมินกลางได้รับการแจ้งเตือนของทุกสาขา',
            audience: 'central',
            text: 'คุณจะเห็นการแจ้งเตือนจากนักศึกษาทุกสาขา รวมถึงนักศึกษาที่ยังไม่มีสาขา แอดมินสาขาจะเห็นการแจ้งเตือนเดียวกันเฉพาะของสาขาตัวเอง'
          },
          {
            heading: 'การแจ้งเตือนเฉพาะสาขาของคุณ',
            audience: 'branch',
            text: 'คุณจะได้รับการแจ้งเตือนเฉพาะคำขอจากนักศึกษาในสาขาของคุณ คำขอของนักศึกษาสาขาอื่นหรือที่ยังไม่มีสาขาจะไปที่แอดมินของสาขานั้นและแอดมินกลาง'
          }
        ]
      }
    }
  },
}
