export default {
  skillMetrics: {
    exposureShort: 'Skill Exposure',
    level: 'Skill Level',
    exposure: 'Exposure Hours',
    activities: 'Activities',
    noData: 'No skill data',
    externalNoComparison: 'Population comparison is not available for external activities'
  },
  skillSources: {
    major: "Major Activities",
    faculty: "Faculty Activities",
    external: "External Activities",
    externalTitle: "External Activity Skills",
    externalHint: "Skills from this student's approved external activities only.",
    externalEmpty: "No approved external activity skill data yet.",
    strongestExternal: "Strongest External Skill",
    internalActivities: "University Activities",
    activitiesUsed: "Activities used",
    sourceLabel: "Activity source",
    sourceCaption: "Source",
    personalSource: "Approved External Activities"
  },
  activityHours: {
    major: 'Major Activity Hours',
    faculty: 'Faculty Activity Hours',
    external: 'External Activity Hours',
    label: 'Activity Hours',
    total: 'Total Activity Hours',
    unit: 'Hours',
    invalid: 'Enter positive hours with up to two decimal places.',
    invalidEdit: 'Enter zero or positive hours with up to two decimal places.'
  },
  common: {
    language: 'Language',
    thai: 'Thai',
    english: 'English',
    helpCenter: 'Help Center',
    helpCenterContact: 'Contact by email:',
    logout: 'Logout',
    settings: 'Settings',
    branchLabel: 'Branch',
    allBranches: 'All Branches',
    facultyActivities: 'Faculty-wide Activities',
    myBranchAndFaculty: 'My Branch & Faculty-wide',
    myBranchOnly: 'My Branch Only'
  },

  adminSidebar: {
    faculty: 'Faculty of Science',
    subtitle: 'UNIVERSITY PORTAL',

    dashboard: 'Dashboard',
    activities: 'Activities',
    studentSkills: 'Student Skills',
    approvals: 'Approvals',

    centralAdmin: 'Central admin · All majors',
    majorPrefix: 'Major:',

    userGuide: 'User Guide',
    openSidebar: 'Open sidebar',
    closeSidebar: 'Close sidebar'
  },

  studentSidebar: {
    faculty: 'Faculty of Science',
    subtitle: 'STUDENT PROGRESS TRACKER',

    myActivities: 'My Activities',
    mySkills: 'My Skills',
    addExternalActivity: 'Add External Activity',
    transcript: 'Transcript',

    userGuide: 'User Guide',
    openSidebar: 'Open sidebar',
    closeSidebar: 'Close sidebar'
  },

  unsavedChanges: {
    title: 'Not finished yet',
    message: 'Your work has not been saved. Do you want to discard it?',
    stay: 'Stay',
    leave: 'Discard',
    createActivity: 'Creating this activity is not finished. What you entered will be lost. Discard it?',
    editActivity: 'Your changes to this activity have not been saved. Discard them?',
    importParticipants: 'The import is not finished. The students you selected will be lost. Discard it?',
    addStudent: 'Adding the student is not finished. Discard it?',
    importStudents: 'The student import is not finished (not confirmed yet). Discard it?',
    transcriptHeader: 'Your transcript header changes have not been saved. Discard them?',
    addAdmin: 'Adding the admin is not finished. Discard it?',
    editStudent: 'Your changes to this student are not saved. Discard them?'
  },

  studentCalendar: {
    title: 'Activity Calendar',
    description: 'Activities organized by the faculty and your major. Plan ahead and click an activity for details.',
    sourceLabel: 'Organized by',
    locationLabel: 'Location',
    hoursLabel: 'Activity hours',
    joinLabel: 'Participation',
    joinedAsParticipant: 'Joined (participant)',
    joinedAsOrganizer: 'Joined (organizer)',
    notJoined: 'Not joined yet',
    sources: {
      faculty: 'Faculty (faculty-wide)',
      major: 'Your major',
      external: 'External activity'
    }
  },

  activityCalendar: {
    title: 'Activity Calendar',
    description: 'All activities, past and upcoming. Click an activity to see its details.',
    previousMonth: 'Previous month',
    nextMonth: 'Next month',
    today: 'Today',
    legendUpcoming: 'Upcoming / ongoing',
    legendPast: 'Past',
    legendCancelled: 'Cancelled',
    more: '+{count} more',
    empty: 'No activities this month',
    loadError: 'Could not load activities',
    close: 'Close',
    dateLabel: 'Date',
    organizerLabel: 'Organizer',
    participantsLabel: 'Participants',
    participantsCount: '{count} people',
    branchLabel: 'Branch',
    facultyWide: 'Faculty-wide activity',
    viewDetails: 'View activity details →',
    statusUpcoming: 'Upcoming',
    statusOngoing: 'Ongoing',
    statusPast: 'Past',
    statusCancelled: 'Cancelled',
    typeLabel: 'Type',
    scopeLabel: 'Show activities',
    scopeAll: 'All activities',
    scopeMine: '{major} only',
    types: {
      academic: 'Academic',
      seminar: 'Seminar',
      training: 'Training / Workshop',
      volunteer: 'Volunteer',
      skill: 'Skill development',
      recreation: 'Recreation',
      other: 'Other'
    }
  },

  adminDashboard: {
  title: 'Dashboard',
  subtitle: 'Overview of faculty activities and student participation',

  activities: 'Activities',
  students: 'Students',
  participants: 'Participants',
  completionRate: 'Completion Rate',

  activityGrowth: 'Activity Growth',
  activityGrowthDescription: 'Number of activities created over time',

  monthly: 'MONTHLY',
  quarterly: 'QUARTERLY',

  skillDistribution: 'Faculty Skill Distribution',
  skillDescription: 'Average proficiency levels across core competencies',

  criticalThinking: 'CRITICAL THINKING',
  communication: 'COMMUNICATION',
  leadership: 'LEADERSHIP',

  averageScore: 'AVG SCORE',

  systemStatus: 'SYSTEM STATUS',
  loadingData: 'LOADING DATA',
  waitingBackend: 'WAITING FOR BACKEND',
  ready: 'READY',

  dashboardHistory: 'Dashboard History',
  dashboardHistoryDescription: 'Select the academic year and semester to view the historical summary, activity growth, and skill distribution.',
  academicYear: 'Academic Year',
  semester: 'Semester',
  allSemesters: 'All Semesters',
  semester1: 'Semester 1',
  semester2: 'Semester 2',
  participantRole: 'PARTICIPANT',
  staffRole: 'STAFF',
  activitiesUnit: 'activities',
  noData: 'no data',
  monthJan: 'JAN',
  monthFeb: 'FEB',
  monthMar: 'MAR',
  monthApr: 'APR',
  monthMay: 'MAY',
  monthJun: 'JUN',
  monthJul: 'JUL',
  monthAug: 'AUG',
  monthSep: 'SEP',
  monthOct: 'OCT',
  monthNov: 'NOV',
  monthDec: 'DEC',
  quarterQ1: 'Q1',
  quarterQ2: 'Q2',
  quarterQ3: 'Q3',
  quarterQ4: 'Q4'
 },

 adminStudentSkills: {
  title: 'Student Skills',
  subtitle: 'Overview of student skill proficiency across the faculty',

  averageSkillScore: 'AVERAGE SKILL SCORE',
  thisSemester: '— this semester',
  studentsEvaluated: 'STUDENTS EVALUATED',
  ofTotalFaculty: 'of total faculty',

  facultyRadar: 'Faculty Proficiency Radar',
  actualProficiency: 'Actual Proficiency',
  benchmarkLevel: 'Benchmark Level',

  leadership: 'Leadership',
  criticalThinking: 'Critical Thinking',
  communication: 'Communication',
  teamwork: 'Teamwork',
  creativity: 'Creativity',
  digitalLiteracy: 'Digital Literacy',

  topArea: 'TOP AREA',
  facultyAverage: 'Faculty average',
  highestScore: 'Highest proficiency score',

  growthArea: 'GROWTH AREA',
  actionPlan: 'Action Plan',

  individualSkills: 'Individual Skills',
  searchPlaceholder: 'ID or Student Name...',
  filterStudents: 'Filter Students',
  primarySkill: 'Primary Skill',
  scoreAverage: 'Score Average',

  studentName: 'Student Name',
  studentId: 'Student ID',
  scoreAvg: 'Score Avg.',
  action: 'Action',
  viewRadar: 'View Radar',
  viewActivities: 'View Activities',
  noStudentData: 'No student skill data available',

  major: 'Major',

  cohortFilterTitle: 'Show skills for',
  yearLevelFilterLabel: 'Class year',
  allYearLevels: 'All class years',
  yearLevel1: '1st Year',
  yearLevel2: '2nd Year',
  yearLevel3: '3rd Year',
  yearLevel4: '4th Year',
  yearLevel5Plus: '5th Year+',
  yearLevelUnknown: 'Unknown year',
  yearLevelColumn: 'Class Year',
  yearLevelHint: 'Class year comes from the entry year in the student ID (first 2 digits); students move up a year each July',
  groupAverage: 'Group average',

  radarViewLabel: 'View',
  radarViewOverall: 'Overall',
  radarViewByYear: 'By class year',
  radarViewByMajor: 'By major',
  radarViewByMajorYear: 'By major × class year',
  radarGroupHint: 'Pick up to 3 groups to draw on the radar',
  avgShort: 'Avg',
  showGroupTable: 'Show numbers for each group',
  groupColumn: 'Group',
  studentsColumn: 'Students',
  skillShortArtsCultureTraditions: 'Arts',
  skillShortVolunteerism: 'Volunteer',
  skillShortAcademics: 'Academics',
  skillShortInternationalization: 'Intl.',
  skillShortHealthPromotion: 'Health',
  skillShortNatureEnvironmentalConservation: 'Nature',
  skillShortCreativeLeadership: 'Leadership',
  skillShortInnovation: 'Innovation',
  skillShortEntrepreneurship: 'Entrepreneur',
  skillShortPromoteEquality: 'Equality',
  skillShortAcademic: 'Academic',
  skillShortNatureEnvironmental: 'Nature',
  skillTrackLabel: 'Skill set',
  skillTrackParticipant: 'Participant skills',
  skillTrackStaff: 'Staff skills',
  skillTrackStaffHint: 'Staff skills come from activities where students were organizers.',
  majorFilterLabel: 'Major',
  allMajors: 'All majors',
  majorNotSpecified: 'Not specified',
  clearCohortFilters: 'Clear',
  ofSelectedGroup: 'of students in this group',

  skillAnalysis: 'Skill Proficiency Analysis',
  skillAnalysisSub: "Student skill profile compared with their major's average and the faculty average.",

  student: 'Student',
  facultyAvg: 'Faculty Avg',
  facultyAvgShort: 'Faculty Avg',
  strongestSkill: 'STRONGEST SKILL',
  studentScore: 'Student score',
  overallAverage: 'Overall average',

  skillGapAnalysis: 'Skill Gap Analysis',
  skillGapSub: 'Skills below the faculty average for this semester.',
  skillGapSubMajor: "Skills below the average of this student's major for this semester.",
  belowFacultyAverage: 'below faculty average',
  belowMajorAverage: 'below major average',
  majorAvgShort: 'Major Avg',
  gapCompareLabel: 'Compare with',
  skillAnalysisSubMajor: "Skills from this student's major activities compared with the major average. External activities are not included.",
  skillAnalysisSubFaculty: 'Skills from faculty activities compared with the faculty average. External activities are not included.',
  studentMajorActivities: 'Student (major activities)',
  studentFacultyActivities: 'Student (faculty activities)',
  gapCompareMajor: 'Major',
  gapCompareFaculty: 'Faculty',
  studentExternalActivities: 'Student (external activities)',
  faculty: 'Faculty',

  recommendation: 'Recommendation:',
  noSignificantGaps: 'No significant skill gaps',
  noGapSub: 'This student is at or above the faculty average across all six skills.',
  noGapSubMajor: "This student is at or above their major's average across all six skills.",

  allSkills: 'All Skills',
  allScores: 'All Scores',

  periodAll: 'All Year',
  periodSemester1: 'Semester 1 (Jan–Jun)',
  periodSemester2: 'Semester 2 (Jul–Dec)',
  yearLabel: 'Year',

  benchmarkButton: 'Benchmark',
  benchmarkModalTitle: 'Set Benchmark Level',
  benchmarkModalSubtitle: 'Set a target for each skill from 1.0 to 5.0 and save it to the database.',
  cancel: 'Cancel',
  saveBenchmark: 'Save Benchmark',
  savingBenchmark: 'Saving...',
  benchmarkRangeError: 'All benchmark scores must be between 1.0 and 5.0',

  loadErrorFallback: 'Cannot load student skill data',
  saveBenchmarkErrorFallback: 'Cannot save benchmark',

  notAvailable: 'N/A',
  belowScore3: 'Below 3.0',

  activitiesAttended: 'Activities Attended',
  activitiesUnit: 'activities',
  joinedPrefix: 'Joined',
  idLabel: 'ID',

  studentDetailAriaLabel: 'Student skill details for',
  closeStudentDetails: 'Close student details',

  activityHistoryTitle: 'Student Activity History',
  activityHistoryAriaLabel: 'Student activity history for',
  closeActivityHistory: 'Close activity history',
  activityHistoryLoading: 'Loading activity history...',
  activityHistoryError: 'Failed to load activity history',
  noActivityHistory: 'This student has no activity history yet',
  activityNameColumn: 'Activity Name',
  activityTypeColumn: 'Type',
  activityDateColumn: 'Date',
  activityRoleColumn: 'Role',
  activityStatusColumn: 'Status',
  activityTypeFaculty: 'Faculty Activity',
  activityTypeExternal: 'External Activity',
  roleParticipant: 'Participant',
  roleOrganizer: 'Organizer',
  statusApproved: 'Approved',
  statusPending: 'Pending',
  statusRejected: 'Rejected',

  skillArtsCultureTraditions: 'Arts, Culture, and Traditions',
  skillVolunteerism: 'Volunteerism',
  skillAcademics: 'Academics',
  skillInternationalization: 'Internationalization',
  skillHealthPromotion: 'Health Promotion',
  skillNatureEnvironmentalConservation: 'Nature & Environmental Conservation',
  skillCreativeLeadership: 'Creative Leadership',
  skillInnovation: 'Innovation',
  skillEntrepreneurship: 'Entrepreneurship',
  skillPromoteEquality: 'Promote Equality',
  skillAcademic: 'Academic',
  skillNatureEnvironmental: 'Nature and Environmental',

  growthPlanArtsCultureTraditions: 'Add more arts, culture, and tradition activities with genuine student participation.',
  growthPlanVolunteerism: 'Add more volunteer and community-service activities with clear roles.',
  growthPlanAcademics: 'Add more academic activities, workshops, and applied projects tied to coursework.',
  growthPlanInternationalization: 'Add more activities that build cross-cultural teamwork and foreign-language use.',
  growthPlanHealthPromotion: 'Add more health-promotion activities and student wellbeing initiatives.',
  growthPlanNatureEnvironmentalConservation: 'Add more ongoing nature, environment, and conservation activities.',
  growthPlanCreativeLeadership: 'Give more students organizer roles that involve leading a team and planning activities.',
  growthPlanInnovation: 'Add more organizer roles in hackathons, innovation projects, and new activity formats.',
  growthPlanEntrepreneurship: 'Add more activities where organizers manage budgets, sponsors, or small ventures.',
  growthPlanPromoteEquality: 'Add more inclusive activities where organizers work on access and fairness for all students.',
  growthPlanAcademic: 'Add more academic seminars, workshops, and study events run by student organizers.',
  growthPlanNatureEnvironmental: 'Add more environmental projects that students lead and organize themselves.',

  recommendationArtsCultureTraditions: 'Join activities involving arts, culture, traditions, and community identity.',
  recommendationVolunteerism: 'Join volunteer projects with clear responsibilities and community impact.',
  recommendationAcademics: 'Join academic workshops, competitions, or project-based learning activities.',
  recommendationInternationalization: 'Join cross-cultural or international activities and practice global collaboration.',
  recommendationHealthPromotion: 'Join health-promotion activities and build sustainable wellness habits.',
  recommendationNatureEnvironmentalConservation: 'Join environmental conservation and sustainability activities.',
  recommendationCreativeLeadership: 'Take an organizer role that involves leading a team or planning an activity.',
  recommendationInnovation: 'Help organize hackathons or innovation projects and try out new ideas.',
  recommendationEntrepreneurship: 'Help manage the budget, sponsors, or fundraising for an activity.',
  recommendationPromoteEquality: 'Help organize inclusive activities that improve access for all students.',
  recommendationAcademic: 'Help organize academic seminars, workshops, or study events.',
  recommendationNatureEnvironmental: 'Help lead or organize environmental and sustainability projects.'
 },

  adminApproval: {
    pageTitle: 'Approvals',
    pageSubtitle: 'Manage requests awaiting review and approval',
    statTotalPending: 'Total Pending',
    statApprovedToday: 'Approved Today',
    statRejectedToday: 'Rejected Today',
    statusTabsAriaLabel: 'Request status',
    pendingTab: 'Pending',
    rejectedTab: 'Rejected',
    pendingRequestsHeading: 'Pending Requests',
    rejectedRequestsHeading: 'Rejected Requests',
    filterButton: 'Filter',
    sortButton: 'Sort',
    filterAllTypes: 'All Types',
    filterSkillValidation: 'Skill Validation',
    filterSpecialRequest: 'Special Request',
    filterExternalActivity: 'External Activity',
    loadingRequests: 'Loading data...',
    noPendingRequests: 'No pending requests',
    noRejectedRequests: 'No rejected requests',
    tableHeaderRequesterName: 'REQUESTER NAME',
    tableHeaderRequestType: 'REQUEST TYPE',
    tableHeaderDateSubmitted: 'DATE SUBMITTED',
    tableHeaderDetails: 'DETAILS',
    tableHeaderActions: 'ACTIONS',
    idLabel: 'ID:',
    viewDetailButton: 'View Detail',
    approveButton: 'Approve',
    rejectButton: 'Reject',
    cancelButton: 'Cancel',
    emptyPlaceholder: '-',
    paginationShowing: 'Showing',
    paginationOf: 'of',
    paginationPendingRequests: 'pending requests',
    detailModalTitle: 'Request Detail',
    detailRequesterLabel: 'Requester',
    detailRequestTypeLabel: 'Request Type',
    detailFieldLabel: 'Detail',
    submittedLabel: 'Submitted',
    reviewEyebrow: 'EXTERNAL ACTIVITY',
    loadingShort: 'Loading...',
    reviewModalAriaLabel: 'External activity detail',
    loadingReviewDetail: 'Loading details...',
    studentLabel: 'Student',
    activityDetailsLabel: 'Activity Details',
    externalOrganizerLabel: 'External Organizer',
    categoryLabel: 'Category',
    roleLabel: 'Role',
    roleOrganizer: 'Organizer',
    roleParticipant: 'Participant',
    dateLabel: 'Date',
    locationLabel: 'Location',
    noDescriptionText: 'No description provided',
    rejectReasonLabel: 'Reason for rejection',
    evidenceLabel: 'Evidence',
    skillMappingLabel: 'Skill Mapping (by student)',
    relatedLabel: 'related',
    staffSkillsLabel: 'Staff skills',
    participantSkillsLabel: 'Participant skills',
    notRelatedLabel: 'Not related',
    levelPrefix: 'Level',
    confirmApprovalTitle: 'Confirm Approval',
    rejectActivityTitle: 'Reject Activity',
    confirmApprovalAriaLabel: 'Confirm approval',
    rejectWithCommentAriaLabel: 'Reject with comment',
    confirmApprovalExternalText: 'Are you sure you want to approve this activity? The activity and the skill mapping set by the student will be counted on the student\'s My Activities page.',
    confirmApprovalGenericText: 'Are you sure you want to approve this request?',
    loadingSkillMapping: 'Loading skill mapping...',
    rejectCommentLabel: 'Comment / Reason for rejection *',
    rejectCommentPlaceholder: 'Explain why this is being rejected or what the student needs to fix, e.g. the evidence file is unclear, please re-upload',
    rejectCommentHint: 'This comment will be sent as a notification to the student immediately',
    confirmApproveButton: 'Confirm Approve',
    confirmRejectButton: 'Confirm Reject',
    loadDetailError: 'Failed to load details',
    rejectReasonRequired: 'Please provide a reason for rejecting, or what the student needs to fix',
    saveFailed: 'Failed to save',
    resultApprovedTitle: 'Approved successfully',
    resultApprovedMessage: "Activity '{name}' has been approved.",
    resultRejectedTitle: 'Rejected successfully',
    resultRejectedMessage: "Activity '{name}' has been rejected.",
    resultOkButton: 'OK',
    loadRequestsError: 'Failed to load data'
  },

  studentActivities: {
    openEvidenceFailed: 'Could not open the evidence file.',
    pageTitle: 'My Activities',
    pageSubtitle: 'Faculty activities you joined and approved external activities.',
    searchPlaceholder: 'Search my activities...',
    clearSearch: 'Clear search',
    totalActivitiesLabel: 'TOTAL ACTIVITIES',
    allTab: 'All',
    facultyActivitiesTab: 'Faculty Activities',
    externalActivitiesTab: 'External Activities',
    mySubmissionsTab: 'My Submissions',
    majorActivitiesTab: 'Major Activities',
    majorActivityLabel: 'Major Activity',
    joinedBadge: 'Joined',
    notJoinedLabel: 'Not joined',
    notJoinedTitle: 'You have not joined this activity',
    notJoinedText: 'This activity is organized by your major. {count} participants have joined so far. Contact the organizer if you would like to take part.',
    noMajorActivitiesLabel: 'Your major has no activities yet',
    noMajorLabel: 'Your profile has no major yet, so major activities cannot be shown',
    filterByDateLabel: 'Filter By Date',
    clearLabel: 'Clear',
    loadingLabel: 'Loading activities...',
    loadActivitiesErrorLabel: 'Cannot load activities',
    statusActive: 'Active',
    statusCompleted: 'Completed',
    statusCancelled: 'Cancelled',
    statusApproved: 'Approved',
    statusPending: 'Pending',
    statusRejected: 'Rejected',
    externalActivityLabel: 'External Activity',
    facultyActivityLabel: 'Faculty Activity',
    roleOrganizer: 'Organizer',
    roleParticipant: 'Participant',
    rejectReasonPrefix: 'Rejection reason:',
    editLabel: 'Edit',
    deleteLabel: 'Delete',
    deletingLabel: 'Deleting...',
    deleteSubmissionConfirm: 'Delete the request "{title}"?\n\nIts evidence file will also be deleted. This cannot be undone.',
    deleteSubmissionFailed: 'Failed to delete the request',
    detailsButtonLabel: 'DETAILS',
    viewActivityDetailsAriaLabel: 'View activity details',
    noActivitiesFoundTitle: 'No activities found',
    tryAnotherLabel: 'Try another activity name or date.',
    noSubmissionsYetLabel: 'No external activity submissions yet.',
    noApprovedActivitiesYetLabel: 'No faculty or approved external activities yet.',
    loadMoreLabel: 'Load More Activities',
    idLabel: 'ID:',
    closeDetailsAriaLabel: 'Close details',
    activityDetailsHeading: 'Activity Details',
    categoryLabel: 'CATEGORY',
    dateLabel: 'DATE',
    sourceDetailLabel: 'SOURCE',
    roleLabel: 'ROLE',
    locationLabel: 'LOCATION',
    organizerLabel: 'ORGANIZER',
    activityDescriptionHeading: 'Activity Description',
    studentReflectionHeading: 'Student Reflection',
    noDescriptionProvided: 'No description provided.',
    viewEvidenceLabel: 'View evidence',
    skillsHeading: 'Skills',
    skillMappingHeading: 'Skill Mapping',
    levelLabel: 'Level',
    noRelatedSkillsLabel: 'No related skills.',
    currentStatusLabel: 'CURRENT STATUS',
    waitingForReviewTitle: 'Waiting for Review',
    waitingForReviewText: 'This submission is waiting for administrator review.',
    activityNotApprovedTitle: 'Activity Not Approved',
    activityNotApprovedFallbackText: 'This activity was not approved.',
    approvedByAdminTitle: 'Approved by Administrator',
    approvedByAdminText: 'This external activity and your Skill Mapping were reviewed and approved.',
    activityCancelledTitle: 'Activity Cancelled',
    activityCancelledText: 'This faculty activity has been cancelled.',
    activityCompletedTitle: 'Activity Completed',
    registeredTitle: 'Registered',
    listedAsRolePrefix: 'You are listed as a',
    listedAsRoleSuffix: 'in this faculty activity.'
  },

  adminCreateActivity: {
    pageTitle: 'Create New Activity',
    stepActivityInfoTitle: 'Activity Info',
    stepActivityInfoSubtitle: 'Activity details',
    stepAttachSkillsTitle: 'Attach Skills',
    stepAttachSkillsSubtitle: 'Set skill levels',
    basicInfoTitle: 'Basic Information',
    basicInfoSubtitle: 'Main information shown on the activity page',
    activityTypeLabel: 'Activity Type',
    selectActivityTypePlaceholder: 'Select activity type',
    customActivityTypePlaceholder: 'Please specify the activity type',
    activityNameLabel: 'Activity Name (Thai/English)',
    activityNamePlaceholder: 'e.g. Bio-Tech Innovations 2026',
    scheduleTitle: 'Schedule',
    scheduleSubtitle: "Choose the activity's start / end date",
    startDateLabel: 'Start Date',
    startDateBadge: 'START DATE',
    endDateLabel: 'End Date',
    endDateBadge: 'END DATE',
    selectDatePlaceholder: 'Select date',
    calendarHeaderSelectStart: 'Select start date',
    calendarHeaderSelectEnd: 'Select end date',
    calendarFooterHintStart: 'You can pick any date you like',
    calendarFooterHintEnd: 'The end date cannot be before the start date',
    todayButton: 'Today',
    orgPersonnelTitle: 'Organization & Personnel',
    orgPersonnelSubtitle: 'Specify the organizing unit, responsible person, and location',
    departmentLabel: 'Organizing Unit (Department/Faculty)',
    departmentPlaceholder: 'e.g. Physics Department',
    responsiblePersonLabel: 'Main Responsible Person',
    responsiblePersonPlaceholder: 'Search for personnel name...',
    advisorLabel: 'Advisor (Responsible Instructor)',
    advisorPlaceholder: "Advisor's name",
    locationLabel: 'Location',
    locationPlaceholder: 'e.g. Room 402, Science Building 3',
    additionalDetailsTitle: 'Additional Details',
    additionalDetailsSubtitle: 'Specify objectives, outcomes, and target audience',
    descriptionLabel: 'Activity Description',
    descriptionPlaceholder: 'Specify objectives, expected outcomes, and target audience...',
    tipsTitle: 'Before You Continue',
    tipsSubtitle: "Check that all key information is complete before setting the activity's skills",
    tipNameAndType: 'Activity name and type',
    tipDates: 'Start / end date',
    tipLocation: 'Activity location',
    skillSettingsLink: 'Skill settings',
    skillsSectionTitle: "Set the Activity's Skills",
    skillsForStaffDescription: 'Skills for activity organizers',
    skillsForParticipantDescription: 'Skills for activity participants',
    staffLabel: 'Staff',
    participantLabel: 'Participant',
    cancelButton: 'Cancel',
    backButton: 'Back',
    continueButton: 'Continue',
    creatingButton: 'Creating...',
    createActivityButton: 'Create Activity',
    weekDays: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    validateOtherActivityTypeRequired: 'Please specify the other activity type',
    validateRequiredFields: 'Please fill in all fields marked with *',
    validateEndDateBeforeStart: 'The end date must not be before the start date',
    backendConnectionError: 'Cannot connect to the Backend',
    backendConnectionErrorHint: 'please check that uvicorn is still running',
    createActivityError: 'Unable to create the activity'
  },

  adminStudentActivities: {
    importParticipantsButton: 'Import Participants',
    importOrganizersButton: 'Import Organizers',
    importRoleNote: 'Everyone will be added as {role} (you can change each role in the review step)',
    importManualTitle: 'Add individually',
    importManualDuplicate: 'This student is already added',
    importOrFile: 'or import from a file',
    selectFileOrStudentError: 'Please add a student or choose a file first',
    previewTableRoleHeader: 'Role',
    downloadTemplateButton: 'Download Template',
    downloadTemplateError: 'Could not download the template. Please try again.',
    activityNameLabel: 'Activity Name *',
    activityNamePlaceholder: 'Activity name',
    activityTypeLabel: 'Activity Type *',
    activityTypePlaceholder: 'Activity type',
    addingStudentLoading: 'Adding...',
    addStudentAction: 'Add Student',
    addStudentFailedDefault: 'Failed to add student',
    addStudentModalEyebrow: 'ADD STUDENT',
    addStudentModalTitle: 'Add Student Manually',
    addStudentSuccessMessage: 'Student added to the activity successfully',
    addStudentValidationError: 'Please fill in student ID, first name, last name, email, major, and role',
    advisorLabel: 'Advisor',
    applyFiltersButton: 'Apply Filters',
    backButton: 'Back',
    backendConnectionError: 'Unable to connect to the backend',
    cancelActivityMenuItem: 'Cancel Activity',
    cancelButton: 'Cancel',
    changeStatusFailedDefault: 'Failed to change activity status',
    confirmImportButton: 'Confirm Import ({count})',
    createActivityButton: 'Create New Activity',
    deleteActivityConfirm: 'Delete this activity?',
    deleteActivityConfirmOk: 'OK',
    deleteActivityConfirmCancel: 'Cancel',
    deleteActivityFailedDefault: 'Failed to delete activity',
    deleteActivityMenuItem: 'Delete Activity',
    departmentLabel: 'Department',
    descriptionLabel: 'Description',
    dropzoneHeading: 'Drag a file here, or click to select a file',
    dropzoneSubtext: 'Supports .csv, .xlsx and .xls files',
    editActivityFailedDefault: 'Failed to update activity',
    editActivityMenuItem: 'Edit Activity',
    editActivityTitle: 'Edit Activity',
    editActivityValidationError: 'Please fill in name, type, date/time, responsible person, and location',
    emailLabel: 'Email *',
    emailPlaceholder: 'student@cmu.ac.th',
    emptyActivitiesTableText: 'No activities yet, or none match your filters',
    endDateTimeLabel: 'End Date / Time *',
    fileReadFailedDefault: 'Unable to read the file',
    filterAllCategoriesOption: 'All Categories',
    filterCategoryLabel: 'CATEGORY',
    filterClearDate: 'Clear date',
    filterDateFromLabel: 'DATE FROM',
    filterDateToLabel: 'DATE TO',
    filterDatePlaceholder: 'Select date',
    filterSearchActivityLabel: 'SEARCH ACTIVITY',
    filterSearchActivityPlaceholder: 'Activity name...',
    filterToday: 'Today',
    firstNameLabel: 'First Name *',
    firstNamePlaceholder: 'First name',
    hideDetailsText: 'Hide details',
    importFailedDefault: 'Import failed',
    importFromFileEyebrow: 'Add members',
    importDuplicateStudentId: 'Duplicate student ID in this list',
    importingLoadingText: 'Importing...',
    importInvalidRole: 'Role must be participant or organizer',
    importIssuesHeading: 'Import Issues',
    importIssuesSubtext: 'Fix these in the table below, or they will be skipped when you confirm the import',
    importMissingEmail: 'Missing email',
    importMissingFirstName: 'Missing first name',
    importMissingLastName: 'Missing last name',
    importMissingStudentId: 'Missing student ID',
    importPreviewEyebrow: 'IMPORT PREVIEW',
    importSuccessDuplicateSuffix: ' (skipped {count} duplicate entries)',
    importSuccessIssueSuffix: ' • skipped {count} problematic entries',
    importSuccessMessage: 'Import successful: {count} people',
    invalidEmailFormat: 'Invalid email format',
    issueStatusLabel: 'Issue',
    lastNameLabel: 'Last Name *',
    lastNamePlaceholder: 'Last name',
    loadingAriaLabel: 'Loading activities',
    locationLabel: 'Location *',
    majorLabel: 'Major *',
    manageActivityEyebrow: 'MANAGE ACTIVITY',
    manageButton: 'Manage',
    markAsCompletedMenuItem: 'Mark as Completed',
    noRelatedSkillsText: 'No related skills',
    noValidImportDataError: 'No data ready to import. Please review the issues first',
    organizerLabel: 'Organizer',
    paginationOf: 'of',
    paginationShowing: 'Showing',
    participantLabel: 'Participant',
    participantSkillsHeading: 'Participant Skills',
    previewEditHint: 'You can edit any cell before importing. Nothing is saved until you click Confirm Import.',
    previewFoundLabel: 'FOUND',
    previewImportButton: 'Preview Import',
    previewIssueNote: "{count} entries have issues and won't be imported unless you fix them. Entries marked Ready can be confirmed as usual.",
    previewIssueRowLabel: 'row',
    previewIssuesLabel: 'ISSUES',
    previewReadyLabel: 'READY',
    previewTableEmail: 'EMAIL',
    previewTableFirstName: 'FIRST NAME',
    previewTableLastName: 'LAST NAME',
    previewTableMajor: 'MAJOR',
    previewTableStatus: 'STATUS',
    previewTableStudentId: 'STUDENT ID',
    quickSearchPlaceholder: 'Quick search activities...',
    readingLoadingText: 'Reading...',
    readyStatusLabel: 'Ready',
    removeFileTooltip: 'Remove file',
    reopenActivityMenuItem: 'Reopen Activity',
    responsiblePersonLabel: 'Responsible Person *',
    roleFieldLabel: 'Role *',
    saveChangesButton: 'Save Changes',
    savingLoadingText: 'Saving...',
    selectMajorPlaceholder: 'Select major',
    selectRolePlaceholder: 'Select Role',
    showDetailsText: 'Show details',
    skillLevelLabel: 'Level',
    skillsLabel: 'Skills',
    skillsToggleLabel: 'Skills',
    staffLabel: 'Staff',
    staffSkillsHeading: 'Staff Skills',
    startDateTimeLabel: 'Start Date / Time *',
    statusActive: 'Active',
    statusCancelled: 'Cancelled',
    statusCompleted: 'Completed',
    statusFieldLabel: 'Status',
    studentAlreadyInActivity: 'This student already exists in the activity',
    studentIdLabel: 'Student ID *',
    studentIdPlaceholder: 'e.g. 670510001',
    studentSearchPlaceholder: 'Type a student ID or name to search',
    studentLookupLoading: 'Searching...',
    studentIdNotFoundError: 'No student found with this ID.',
    facultyLabel: 'Faculty',
    noMajorLabel: 'No major',
    summaryActiveActivities: 'ACTIVE ACTIVITIES',
    summaryParticipantsMonth: 'PARTICIPANTS (MONTH)',
    summaryPendingEvaluations: 'PENDING EVALUATIONS',
    tableHeaderActivityName: 'ACTIVITY NAME',
    sortByStartDate: 'Sort by start date',
    sortByLatest: 'Sort by latest',
    sortAriaLabel: 'Sort activities',
    sortDirectionAsc: 'Oldest first (click to reverse)',
    sortDirectionDesc: 'Newest first (click to reverse)',
    tableHeaderDetails: 'DETAILS',
    tableHeaderEndDate: 'END DATE',
    tableHeaderManageActivity: 'MANAGE ACTIVITY',
    tableHeaderManageParticipants: 'MANAGE PARTICIPANTS',
    tableHeaderOrganizer: 'ORGANIZER',
    tableHeaderParticipants: 'PARTICIPANTS',
    tableHeaderStartDate: 'START DATE',
    unknownStudentFallback: 'Unknown student',
    unsupportedFileTypeError: 'Only .csv, .xlsx and .xls files are supported',
    viewDetailButton: 'View Detail',
    weekdayFri: 'Fr',
    weekdayMon: 'Mo',
    weekdaySat: 'Sa',
    weekdaySun: 'Su',
    weekdayThu: 'Th',
    weekdayTue: 'Tu',
    weekdayWed: 'We'
  },

  studentExternalActivity: {
    editTitle: 'Edit & Resubmit Activity',
    addTitle: 'Add External Activity',
    editSubtitle: 'Edit the details of a rejected activity, then resubmit it for admin review.',
    addSubtitle: 'Submit an activity you took part in outside the faculty, along with evidence and skill mapping, for admin review and approval.',
    activityDetailsHeading: 'Activity Details',
    activityNameLabel: 'Activity Name',
    activityNamePlaceholder: 'Enter the name of the activity you joined',
    organizerLabel: 'External Organizer',
    organizerPlaceholder: 'Organization / entity that hosted the activity',
    categoryLabel: 'Activity Category',
    selectCategoryOption: 'Select category',
    otherCategoryModalTitle: 'Please specify the activity category',
    otherCategoryInputPlaceholder: 'Type your activity category',
    otherCategoryConfirmButton: 'Confirm',
    otherCategoryCancelButton: 'Cancel',
    otherCategoryRequiredError: 'Please specify the activity category',
    otherCategoryDisplayLabel: 'Specified category',
    otherCategoryEditButton: 'Edit',
    roleLabel: 'Your Role',
    selectRoleOption: 'Select your role',
    descriptionLabel: 'Activity Description / Reflection',
    descriptionPlaceholder: 'Describe what you did and what you learned from this activity...',
    startDateLabel: 'Start Date',
    startDatePlaceholder: 'Select start date',
    endDateLabel: 'End Date',
    endDatePlaceholder: 'Select end date',
    locationLabel: 'Location',
    locationPlaceholder: 'Specify place or online link',
    uploadEvidenceLabel: 'Upload Evidence',
    uploadEvidenceHint: 'Certificate or photo from participation · Up to {max} files · JPG, PNG, PDF, max 5MB each',
    chooseFileButton: 'Click to choose file',
    currentEvidenceLabel: 'Current evidence',
    addMoreFilesButton: 'Add more files',
    newEvidenceLabel: 'New file',
    evidenceListHeading: 'Evidence files',
    evidenceCountLabel: '{count}/{max} files',
    evidenceLimitReached: 'You have attached {max} files. Remove a file to add another.',
    evidenceLimitError: 'You can attach up to {max} evidence files per request',
    removeFileAriaLabel: 'Remove file',
    submittingButton: 'Submitting...',
    resubmittingButton: 'Resubmitting...',
    submitButton: 'Submit for Approval',
    resubmitButton: 'Resubmit for Approval',
    skillMappingHeading: 'Skill Mapping',
    skillMappingSubtitle: 'Evaluate the level of the skills you developed (1-5)',
    participantTab: 'Participant',
    staffTab: 'Staff',
    skillsFieldLabel: 'Skills gained',
    skillsFieldHint: 'The skill set changes based on your role',
    viewSkillsButton: 'View skills',
    adjustSkillsButton: 'Adjust skill levels',
    evidenceCardHeading: 'Participation evidence',
    skillsSelectedSingular: '{count} skill selected',
    skillsSelectedPlural: '{count} skills selected',
    skillsNoneSelected: 'No skills selected',
    skillsModalSave: 'Save',
    skillsModalCancel: 'Cancel',
    skillsModalClose: 'Close',
    loadEditFailed: 'Failed to load the activity to edit',
    editNotFound: 'Could not find the activity to edit, or this activity cannot be edited',
    fileTypeError: 'The evidence file must be .jpg, .jpeg, .png, or .pdf',
    fileEmptyError: 'The evidence file is empty',
    fileSizeError: 'The evidence file must not exceed 5MB',
    requiredFieldsError: 'Please fill in all fields marked with *',
    dateRangeError: 'The end date must not be before the start date',
    skillRequiredError: 'Please select at least 1 related skill (use "Adjust skill levels")',
    evidenceRequiredError: 'Please attach an evidence file (certificate or photo)',
    submitFailedFallback: 'Failed to submit the activity',
    confirmSubmitTitle: 'Confirm Submission',
    confirmSubmitMessage: "Do you want to submit the activity '{name}' for approval?",
    confirmResubmitTitle: 'Confirm Resubmission',
    confirmResubmitMessage: "Do you want to resubmit the edited activity '{name}' for approval?",
    confirmCancelButton: 'Cancel',
    confirmSubmitButton: 'Confirm',
    connectionError: 'Could not connect to the backend'
  },

  studentSkills: {
    loading: 'Loading skill data...',
    retry: 'Retry',
    title: 'My Skills',
    year: 'Year',
    radarChartTitle: 'Skill Overview - Radar Chart View',
    skillRadar: 'Skill Radar',
    noDataInPeriod: 'No skill data available for this period yet',
    activitiesUsedTitle: 'Activities Used to Calculate Skills',
    activitiesUnit: 'activities',
    tableActivityName: 'ACTIVITY NAME',
    tableDescription: 'DESCRIPTION',
    tableSkillsGained: 'SKILLS GAINED',
    tableDate: 'DATE',
    tableStatus: 'STATUS',
    noActivityData: 'No activity data available',
    noActivityDataSubtitle: 'Activities used to calculate skills will appear here',
    loadError: 'Failed to load skill data',
    connectionError: 'Cannot connect to Backend',
    skillTrackLabel: 'Skill set',
    participantSkillsOption: 'Participant skills',
    participantColumnHeading: 'Participant skills',
    staffColumnHeading: 'Staff skills',
    overallSkillsOption: 'Overall skills',
    overallTrackHint: 'Combines participant skills (from activities you joined) and staff skills (from activities you organized) in one 12-skill chart',
    radarChartTitleOverall: 'All Skills Overview (Participant + Staff) - Radar Chart',
    noDataInPeriodOverall: 'No skill data in this period yet',
    activitiesUsedTitleOverall: 'Activities used for skills (participant + staff)',
    noActivityDataOverall: 'No activities in this period',
    noActivityDataSubtitleOverall: 'Activities you joined or organized will appear here',
    staffSkillsOption: 'Staff skills',
    staffTrackHint: 'Staff skills are calculated only from activities where you were an organizer (staff).',
    radarChartTitleStaff: 'Staff Skill Overview - Radar Chart View',
    noDataInPeriodStaff: 'No staff skill data for this period yet',
    activitiesUsedTitleStaff: 'Organizer Activities Used to Calculate Staff Skills',
    noActivityDataStaff: 'No organizer activities in this period',
    noActivityDataSubtitleStaff: 'Activities where you were an organizer (staff) will appear here',
    comparisonLabel: 'Compare with',
    comparisonMajorOption: 'Major activities',
    comparisonFacultyOption: 'Faculty activities',
    comparisonMajorHint: 'Compares your skills from your major\'s activities with the average of students in your major. External activities are not included.',
    comparisonFacultyHint: 'Compares your skills from faculty-wide activities with the average of all students in the faculty. External activities are not included.',
    comparisonNoMajor: 'Your profile has no major, so there is no major comparison.',
    mySkillsMajorLegend: 'My skills (major activities)',
    mySkillsFacultyLegend: 'My skills (faculty activities)',
    majorAverageLegend: 'Major average',
    facultyAverageLegend: 'Faculty average',
    scopeMajor: 'Major',
    scopeFaculty: 'Faculty',
    scopeExternal: 'External',
    scopeOtherMajor: 'Other major',
    comparisonExternalOption: 'External activities',
    comparisonExternalHint: 'Shows your skills from approved external activities.',
    mySkillsExternalLegend: 'My skills (external activities)',
    statusActive: 'Active',
    statusCompleted: 'Completed',
    statusApproved: 'Approved',
    statusPending: 'Pending',
    statusRejected: 'Rejected',
    statusCancelled: 'Cancelled'
  },

  adminParticipantDetails: {
    eyebrowActivityManagement: 'ACTIVITY MANAGEMENT',
    pageTitle: 'Participant Details',
    pageSubtitle: 'Review and edit participant information',
    backButton: 'Back to Activities',
    activityLabel: 'ACTIVITY',
    participantsLabel: 'PARTICIPANTS',
    organizersLabel: 'ORGANIZERS',
    totalMembersLabel: 'TOTAL MEMBERS',
    activityDetailsLabel: 'ACTIVITY DETAILS',
    typeLabel: 'TYPE',
    dateLabel: 'DATE',
    locationLabel: 'LOCATION',
    responsibleLabel: 'RESPONSIBLE',
    descriptionLabel: 'DESCRIPTION',
    noDescriptionText: 'No additional description',
    readMoreButton: 'Read more',
    skillsGainedTitle: 'Skills Gained by Role',
    skillsGainedSubtitle: 'Skill levels each member earns from this activity, depending on their role',
    participantSkillSetLabel: 'Participant skills',
    staffSkillSetLabel: 'Staff skills',
    skillLevelLabel: 'Level',
    noSkillsForRoleText: 'No skills set for this role',
    studentsInActivityTitle: 'Students in Activity',
    studentsInActivitySubtitle: 'Click Edit to update an entire row at once, or Remove to take a student out of this activity',
    studentsCountSuffix: 'students',
    loadingText: 'Loading data...',
    studentIdHeader: 'STUDENT ID',
    studentNameHeader: 'STUDENT NAME',
    facultyHeader: 'FACULTY',
    majorHeader: 'MAJOR',
    roleHeader: 'ROLE',
    actionsHeader: 'ACTIONS',
    firstNamePlaceholder: 'First name',
    lastNamePlaceholder: 'Last name',
    savingButton: 'Saving',
    saveButton: 'Save',
    editButton: 'Edit',
    removeButton: 'Remove',
    removingButton: 'Removing',
    participantRole: 'Participant',
    organizerRole: 'Organizer',
    modalActivityDescriptionLabel: 'ACTIVITY DESCRIPTION',
    activityDescriptionModalTitle: 'Activity Description',
    closeButtonAriaLabel: 'Close',
    loadFailedError: 'Failed to load data',
    accessDeniedError: 'You do not have permission to view this activity. Redirecting to the activity list...',
    fillAllFieldsError: 'Please fill in all required fields',
    saveFailedError: 'Failed to save data',
    saveFailedFallbackError: 'Unable to save data',
    removeParticipantConfirm: 'Remove {name} ({id}) from this activity?\n\nThe student record and their other activities will be kept.',
    removeFailedError: 'Failed to remove student'
  },

  studentNotifications: {
    title: 'Notifications',
    markAllRead: 'Mark all as read',
    empty: 'No notifications yet',
    loadError: 'Could not load notifications',
    justNow: 'Just now',
    unread: 'Unread',
    approved: "Your activity '{title}' has been approved ✓",
    rejected: "Your activity '{title}' was rejected - {reason}",
    requestApproved: "Your request '{title}' has been approved ✓",
    requestRejected: "Your request '{title}' was rejected - {reason}",
    loadMore: 'Show more',
    loadingMore: 'Loading...',
    clearAll: 'Clear all',
    cancel: 'Cancel',
    confirmClear: 'Delete',
    clearing: 'Deleting...',
    clearFailed: 'Could not delete. Please try again.',
    clearConfirm: 'Delete all notifications? This cannot be undone.'
  },

  studentContact: {
    title: 'Contact Us',
    message: 'If you have any questions or need assistance, please contact us',
    channelsTitle: 'Contact channels',
    comingSoon: 'Contact details coming soon'
  },

  studentLayout: {
    notifications: 'Notifications',
    unread: 'unread',
    markAllRead: 'Mark all read',
    noNotifications: 'No notifications.',
    toggleSidebar: 'Toggle sidebar',
    myProfile: 'My Profile',
    studentProfileAlt: 'Student profile',
    idLabel: 'ID',
    faculty: 'Faculty',
    major: 'Major',
    email: 'Email',
    cannotLoadNotifications: 'Cannot load notifications',
    logoutAndSwitchStudent: 'Log out / switch student'
  },

  adminLogin: {
    title: 'Admin Login',
    subtitle: 'Faculty of Science',
    signInButton: 'Sign In',
    loading: 'Loading...',
    bypassNotice: 'Test mode: pick or type a test admin email. No password needed.',
    emailLabel: 'Admin email',
    emailPlaceholder: 'e.g. central@test.local',
    accountsTitle: 'Test admin accounts',
    centralMajor: 'Central admin (all majors)',
    unknownEmail: 'This email is not in the test admin list.',
    sessionExpired: 'Please choose an admin email again.',
    backendUnavailable: 'Cannot reach the backend. Check that it is running.',
    retry: 'Try again',
    bypassDisabledTitle: 'Admin test mode (bypass) is not enabled, so admin pages are unavailable.',
    bypassDisabledStep1: '1. Add this line to the .env file in the project root',
    bypassDisabledStep2: '2. Restart the backend, then click "Try again"'
  },

  studentLogin: {
    loginTitle: 'Sign in',
    loginSubtitle: 'Use your email and password, for both students and admins',
    languageLabel: 'Language',
    sessionExpired: 'Your session has expired or your account changed. Please sign in again.',
    universityName: 'Chiang Mai University',
    facultyName: 'Faculty of Science',
    adminLogin: 'Admin Login',
    emailLabel: 'Email',
    emailPlaceholder: 'name@example.com',
    passwordLabel: 'Password',
    showPassword: 'Show password',
    hidePassword: 'Hide password',
    rememberMe: 'Remember Me',
    forgotPassword: 'Forgot Password?',
    signInButton: 'Sign In',
    newToPortal: 'New to the portal?',
    contactItSupport: 'Contact IT Support',
    forAccess: 'for access.',
    emailRequiredError: 'Please enter your email',
    passwordRequiredError: 'Please enter your password',
    invalidCredentialsError: 'Incorrect email or password',
    emailNotFoundError: 'This email was not found in the system',
    wrongPasswordError: 'Incorrect password',
    authUnavailableError: 'Sign-in is temporarily unavailable. The backend authentication configuration needs attention.',
    backendUnavailableError: 'Could not reach the backend. Please try again.'
  },

  skillLevelEditor: {
    notRelated: 'Not related',
    level: 'LEVEL',
    notApplicable: 'N/A'
  },

  adminNotifications: {
    title: 'Notifications',
    markAllRead: 'Mark all as read',
    empty: 'No notifications yet',
    loadError: 'Could not load notifications',
    justNow: 'Just now',
    unread: 'Unread',
    externalSubmitted: '{name} submitted an external activity request: {title}',
    externalResubmitted: '{name} edited and resubmitted the external activity request: {title}',
    loadMore: 'Show more',
    loadingMore: 'Loading...',
    clearAll: 'Clear all',
    cancel: 'Cancel',
    confirmClear: 'Delete',
    clearing: 'Deleting...',
    clearFailed: 'Could not delete. Please try again.',
    clearConfirm: 'Clear all notifications from your bell? Other admins still see them.'
  },

  adminSettings: {
    title: 'Settings',
    subtitle: 'System settings for the central admin',
    subtitleBranch: 'Manage {major} students and the transcript header',
    sectionStudentsDescriptionBranch: 'Import and manage {major} students',
    importBranchNote: 'You can only import {major} students. Rows with an empty major are set to {major} automatically.',
    deleteAllMessageBranch: 'Are you sure you want to delete all {count} {major} students from the system? This action cannot be undone (students in other majors are not affected).',
    importTitle: 'Import Students',
    importDescription: 'Upload an Excel or CSV file to add new students. Student IDs that already exist are skipped.',
    downloadTemplate: 'Download Template',
    templateError: 'Could not download the template',
    exportStudents: 'Export Students',
    exportStudentsError: 'Could not export students',
    requiredColumns: 'Columns in the file',
    dropzoneTitle: 'Drag a file here, or click to choose a file',
    dropzoneHint: '.xlsx, .xls or .csv, up to 5MB',
    chooseFile: 'Choose file',
    fileTypeError: 'Only .xlsx, .xls and .csv files are supported',
    fileSizeError: 'File is larger than 5MB',
    reading: 'Reading file...',
    requestError: 'Something went wrong. Please try again.',
    previewTitle: 'Review before importing',
    previewHint: 'Check the rows below, then click \'Confirm Import\' to save only the new students.',
    columnRow: 'Row',
    columnStudentId: 'Student ID',
    columnFirstName: 'First name',
    columnLastName: 'Last name',
    columnEmail: 'Email',
    columnMajor: 'Major',
    columnStatus: 'Status',
    statusNew: 'New',
    statusDuplicate: 'Duplicate (skipped)',
    statusInvalid: 'Invalid',
    summaryTotal: 'Total',
    summaryNew: 'To import',
    summarySuccess: 'Imported',
    summarySkipped: 'Skipped (duplicate)',
    summaryFailed: 'Invalid',
    noNewRows: 'There are no new students to import',
    emptyFile: 'No student rows were found in the file',
    confirmImport: 'Confirm Import',
    importing: 'Importing...',
    chooseAnotherFile: 'Choose another file',
    resultTitle: 'Import complete',
    issuesTitle: 'Rows not imported',
    importAnother: 'Import another file',
    studentsTitle: 'All Students',
    studentsDescription: 'View and manage every student in the system',
    studentsDescriptionBranch: 'View and manage {major} students',
    studentsCount: '{count} students',
    studentsFound: '{count} of {all} students',
    searchPlaceholder: 'Search ID, name, email or major',
    deleteAllButton: 'Delete all',
    columnName: 'Name',
    columnActivities: 'Activities',
    columnAdded: 'Added',
    columnActions: 'Actions',
    activitySummary: 'Faculty {faculty} · External {external}',
    noMajor: 'No major',
    noMajorHint: 'Branch admins cannot see this student',
    deleteStudentAria: 'Delete {name}',
    editStudentAria: 'Edit {name}',
    editStudentTitle: 'Edit Student',
    editStudentSubtitle: 'Student ID {id}',
    studentRequiredError: 'Please enter first and last name',
    studentSaveFailed: 'Could not save the student',
    studentUpdated: 'Saved {name}',
    majorCentralOnlyNote: 'Only the central admin can change a student\'s major',
    majorTransferNote: 'Moving from {from} to {to}: past activities still count for the old major, so the student\'s skill graph stays the same. The major comparison will use the new major\'s average.',
    studentsLoading: 'Loading students...',
    studentsLoadError: 'Could not load students',
    retry: 'Retry',
    studentsEmpty: 'There are no students yet',
    studentsNoMatch: 'No students match your search',
    pageInfo: 'Page {page} of {pages}',
    previousPage: 'Previous page',
    nextPage: 'Next page',
    deleteOneTitle: 'Confirm student deletion',
    deleteOneMessage: 'Are you sure you want to delete {name} (ID: {id}) from the system? This action cannot be undone.',
    deleteRelatedWarning: 'This student\'s data will also be deleted: {faculty} faculty activity memberships and {external} external activities (including evidence files).',
    deleteAllTitle: 'Confirm deleting all students',
    deleteAllMessage: 'Are you sure you want to delete all {count} students from the system? This action cannot be undone.',
    deleteAllKeepsActivities: 'Faculty activities created by admins are kept.',
    deleteAllConfirmLabel: 'Type {word} to confirm',
    deleteConfirmWord: 'DELETE',
    cannotUndo: 'This cannot be undone.',
    cancelButton: 'Cancel',
    confirmDeleteButton: 'Confirm delete',
    filterYearLabel: 'Year level',
    allYears: 'All years',
    yearOption: 'Year {n}',
    yearOptionPlus: 'Year {n}+',
    filterMajorLabel: 'Major',
    allMajors: 'All majors',
    showingCount: 'Showing {count} of {all} students',
    columnYear: 'Year',
    selectAllVisible: 'Select all',
    selectStudentAria: 'Select {name}',
    bulkActionsLabel: 'Selected students actions',
    selectedCount: '{count} selected',
    deleteSelected: 'Delete selected',
    clearSelection: 'Clear selection',
    bulkDeleteTitle: 'Confirm deleting selected students',
    bulkDeleteMessage: 'Delete {count} students from the system? This action cannot be undone.',
    bulkDeleteRelated: 'Their activity memberships, external activities, evidence files, requests and notifications will be deleted too.',
    deletedSelected: 'Deleted {count} students',
    deleting: 'Deleting...',
    deleteFailed: 'Could not delete. Please try again.',
    deletedOne: 'Deleted \'{name}\'',
    deletedAll: 'Deleted all {count} students',
    sectionStudents: 'Manage Students',
    sectionAdmins: 'Manage Admins',
    adminsTitle: 'Branch admins',
    adminsDescription: 'Branch admins can only see and manage data of their own branch',
    adminsCount: '{count} admins',
    addAdminButton: 'Add admin',
    columnBranch: 'Branch',
    adminsLoading: 'Loading admins...',
    adminsLoadError: 'Could not load admins',
    adminsEmpty: 'There are no branch admins yet',
    deleteAdminAria: 'Delete admin {name}',
    addAdminTitle: 'Add admin',
    addAdminSubtitle: 'The new branch admin only sees data of the selected branch',
    fieldEmail: 'Email',
    fieldBranch: 'Branch',
    selectBranch: 'Select a branch',
    adminRequiredError: 'Please enter an email and choose a branch',
    adminEmailError: 'Invalid email format',
    adminSaveFailed: 'Could not add the admin. Please try again.',
    saveButton: 'Save',
    saving: 'Saving...',
    adminCreated: 'Added admin \'{name}\'',
    deleteAdminTitle: 'Delete branch admin',
    deleteAdminMessage: 'Delete admin \'{name}\' ({email})?',
    deleteAdminWarning: 'This account will no longer be able to sign in, and is signed out immediately if in use.',
    adminDeleted: 'Deleted admin \'{name}\'',
    viewAll: 'View all ({count})',
    showLess: 'Show less',
    defaultPasswordNote: 'The new admin signs in at /login with this email. The default password is 1234.',
    sectionStudentsDescription: 'Import and manage student records',
    sectionAdminsDescription: 'Add and remove branch admins',
    sectionTranscript: 'Manage Transcript',
    sectionTranscriptDescription: 'Edit the transcript header and signatory',
    manageSection: 'Manage',
    closeSection: 'Close',
    transcriptHeaderTitle: 'Transcript header',
    transcriptHeaderDescription: 'Header text and signatory shown on the transcript PDF (styles A and B)',
    transcriptThai: 'Thai',
    transcriptEnglish: 'English',
    transcriptUniversity: 'University name',
    transcriptFaculty: 'Faculty name',
    transcriptTitle: 'Document title',
    transcriptSignerName: 'Authorized signatory name',
    transcriptSignerPosition: 'Authorized signatory position',
    transcriptHint: 'Applies to transcripts generated after saving. Empty fields use the default (the faded text in each field).',
    transcriptResetDefaults: 'Use defaults',
    transcriptLoading: 'Loading transcript settings...',
    transcriptLoadError: 'Could not load transcript settings',
    transcriptSaveFailed: 'Could not save. Please try again.',
    transcriptPreviewTitle: 'Transcript preview',
    transcriptPreviewDescription: 'Uses a sample student and the values in the form (not saved yet). Updates automatically when you stop typing.',
    transcriptPreviewStyle: 'Style',
    transcriptPreviewLanguage: 'Language',
    transcriptStyleA: 'Style A Classic',
    transcriptStyleB: 'Style B Modern',
    transcriptPreviewRefresh: 'Refresh preview',
    transcriptPreviewLoading: 'Generating preview...',
    transcriptPreviewFailed: 'Could not generate the preview',
    transcriptSaved: 'Transcript header saved. It applies to PDFs generated from now on.'
  },

  studentTranscript: {
    title: 'Activity Transcript',
    subtitle: 'Download your activity transcript (A4 PDF)',
    loading: 'Loading...',
    loadError: 'Could not load transcript options.',
    retry: 'Try again',
    styleTitle: 'Document style',
    styleA: 'Style A · Classic',
    styleADescription: 'Centered header, looped Thai font, bordered tables, skill scores in boxes',
    styleB: 'Style B · Modern',
    styleBDescription: 'Full-width color header, skill bars, clean tables, QR placeholder',
    scopeTitle: 'Activity type',
    scopeAll: 'All activities',
    scopeMajor: 'My major only',
    scopeFaculty: 'Faculty-wide only',
    scopeExternal: 'External only',
    activitiesUnit: 'activities',
    yearTitle: 'Year level',
    currentYear: 'Current year: Year',
    yearRule: 'You can select up to your current year',
    yearUnknown: 'Year level cannot be determined from your student ID, so only "All years" is available.',
    allYears: 'All years',
    yearPrefix: 'Year',
    yearDisabled: 'Above your current year',
    demoNote: 'Demo document with a "SAMPLE" watermark',
    download: 'Download PDF',
    downloading: 'Generating PDF...',
    downloadError: 'Download failed.',
    preview: 'Preview',
    previewTitle: 'Transcript preview',
    previewLoading: 'Generating PDF...',
    close: 'Close',
    previewPopupBlocked: 'Your browser blocked the new tab. Allow pop-ups and try again, or download the PDF.',
    languageTitle: 'Document language',
    languageHint: 'All text in the document uses the selected language. Names and activity titles appear as recorded.',
    languageThai: 'ภาษาไทย (Thai)',
    languageThaiNote: 'Dates and academic years in the Buddhist Era',
    languageEnglish: 'English',
    languageEnglishNote: 'Dates and academic years in the Gregorian calendar',
    previewThai: 'Preview (Thai)',
    previewEnglish: 'Preview (English)',
    downloadThai: 'Download PDF (Thai)',
    downloadEnglish: 'Download PDF (English)'
  },

  studentGuide: {
    title: 'User Guide',
    subtitle: 'How to use the student activity and skill tracking system. Choose a topic below to see the details.',
    jumpTo: 'Jump to',
    expandAll: 'Expand all',
    collapseAll: 'Collapse all',
    openPage: 'Open page',
    tip: 'Tip',
    stillNeedHelp: 'Still have questions? Email the staff at',
    sections: {
      activities: {
        title: 'My Activities',
        summary: 'See every activity you joined, both faculty and external activities',
        topics: [
          {
            heading: 'What is a Faculty Activity?',
            text: 'An activity run by your faculty or your major. When an admin records you as a participant or organizer, it appears on this page automatically. You do not need to submit anything.',
            tip: 'Activities organized by other majors in the faculty appear under the "External Activities" tab.'
          },
          {
            heading: 'What is an External Activity?',
            text: 'An activity held outside the faculty, such as a camp, training, volunteer work or competition run by another organization. You submit the details and evidence yourself from "Add External Activity", and it counts once an admin of your major approves it.'
          },
          {
            heading: 'Viewing activity details',
            steps: [
              'Click an activity card or the "Details" button.',
              'The details window shows the date, location, organizer, your role, the description, and the skills with their levels.',
              'For external activities, click "View evidence" to open the attached files.',
              'The status at the bottom shows whether the activity is approved, waiting for review, or not approved (with the reason).'
            ]
          },
          {
            heading: 'Filtering and searching',
            steps: [
              'Choose a tab: "All", "Faculty Activities", "External Activities" or "My Submissions" (every request you sent, in any status).',
              'Type an activity name in the search box at the top.',
              'Use "Filter By Date" to show a specific date, and "Clear" to remove the filter.',
              'If you have many activities, scroll down and click "Load More Activities".'
            ]
          }
        ]
      },
      external: {
        title: 'Add External Activity',
        summary: 'Submit an activity you joined outside the faculty, with evidence, for admin approval',
        topics: [
          {
            heading: 'Filling in the activity details',
            steps: [
              'Enter the activity name and the organizing organization.',
              'Choose a category. If none fits, choose "Other" (อื่น ๆ) and type your own.',
              'Pick the start and end dates (the end date cannot be before the start date).',
              'Enter the location, or a link for an online activity.',
              'Describe what you did and what you learned.'
            ],
            tip: 'Fields marked with * are required.'
          },
          {
            heading: 'Choosing your role and skills',
            steps: [
              'Choose your role: Participant or Staff (organizer / team member).',
              'The skills panel appears after you choose a role. Each role has its own set of skills.',
              'Click "Adjust skill levels". Every skill starts at level 3; set each from 1 to 5 based on what you actually developed.',
              'For skills unrelated to the activity, tick "Not related".',
              'Keep at least one skill, then click "Save".'
            ]
          },
          {
            heading: 'Attaching evidence',
            text: 'Attach a certificate or photos of you taking part: at least 1 and up to 10 files. JPG, PNG and PDF are supported, up to 5MB each. Click "Click to choose file" to attach, and the X button on a file to remove it.',
            tip: 'Photos that clearly show the activity name, date or you help the admin approve faster.'
          },
          {
            heading: 'Submitting and waiting for approval',
            steps: [
              'Click "Submit for Approval", then "Confirm" in the window that appears.',
              'Your request appears under the "My Submissions" tab of My Activities with the status "Pending".',
              'An admin of your major reviews the details, the evidence and the skill levels.',
              'Once approved, the activity appears under "External Activities" and counts in My Skills and your transcript.'
            ],
            tip: 'While a request is pending you can delete it if you made a mistake (its evidence files are deleted too).'
          },
          {
            heading: 'Fixing a rejected activity',
            steps: [
              'Go to the "My Submissions" tab. A rejected activity shows "Rejected" with the admin\'s reason.',
              'Click "Edit". The form opens with your previous details and evidence.',
              'Make the changes the reason asks for. You can add or remove evidence files.',
              'Click "Resubmit for Approval". The status goes back to "Pending".'
            ]
          }
        ]
      },
      skills: {
        title: 'My Skills',
        summary: 'See an overview of the skills you gained and compare them with the average',
        topics: [
          {
            heading: 'Reading the skill radar chart',
            steps: [
              'Each corner of the chart is one skill. The further a point is from the center, the higher the score (out of 5).',
              'The score is the average skill level from the activities that count.',
              'Choose a year and term (whole year / term 1 / term 2) at the top right to see each period.',
              'Choose the skill set: "Overall skills" combines both sets; "Participant skills" come from activities you joined; "Staff skills" come only from activities you organized.',
              'The table below the chart lists the activities used in the calculation.'
            ]
          },
          {
            heading: 'What each skill means',
            groups: [
              {
                label: 'Participant skills',
                items: [
                  { term: 'Arts, Culture, and Traditions', text: 'Taking part in arts, culture and traditions' },
                  { term: 'Volunteerism', text: 'Volunteering and contributing to society' },
                  { term: 'Academics', text: 'Learning and academic development' },
                  { term: 'Internationalization', text: 'Global outlook and cross-cultural learning' },
                  { term: 'Health Promotion', text: 'Promoting health and well-being' },
                  { term: 'Nature and Environmental Conservation', text: 'Protecting nature and the environment' }
                ]
              },
              {
                label: 'Staff skills',
                items: [
                  { term: 'Creative Leadership', text: 'Leading with creativity' },
                  { term: 'Innovation', text: 'Thinking up and building new ideas' },
                  { term: 'Entrepreneurship', text: 'An entrepreneurial mindset' },
                  { term: 'Promote Equality', text: 'Promoting equality and inclusion' },
                  { term: 'Academic', text: 'Academic skills' },
                  { term: 'Nature and Environmental', text: 'Nature and the environment' }
                ]
              }
            ]
          },
          {
            heading: 'Comparing with the faculty average',
            steps: [
              'Under "Compare with", choose "Faculty activities" to compare with the average of all students in the faculty, or "Major activities" to compare with students in your major.',
              'The chart shows two lines: your skills and the average. The legend below the chart shows which color is which.',
              'Corners where your line is inside the average are skills worth finding more activities for.',
              'The "External activities" option shows only the skills from your external activities, with no average to compare.'
            ],
            tip: 'Major and faculty comparisons leave out external activities, so everyone is compared on the same set of activities.'
          }
        ]
      },
      transcript: {
        title: 'Transcript',
        summary: 'Create an activity certificate as an A4 PDF',
        topics: [
          {
            heading: 'Choosing a transcript style',
            groups: [
              {
                label: 'Document style',
                items: [
                  { term: 'Style A Classic', text: 'Centered header, bordered tables and number boxes for skill scores. Suits formal documents.' },
                  { term: 'Style B Modern', text: 'Colored header band, skill scores as bars and open tables. Easy to read.' }
                ]
              },
              {
                label: 'Activity type',
                items: [
                  { term: 'All activities', text: 'Every activity that counts' },
                  { term: 'Major / faculty / external only', text: 'Only the group you choose. The number next to each option is the activity count.' }
                ]
              }
            ]
          },
          {
            heading: 'Previewing and downloading the PDF',
            steps: [
              'Choose the style, the activity type and the document language.',
              'Click "Preview" to open the PDF on screen (some devices open it in a new tab; if the browser blocks the pop-up, allow it).',
              'Check the details, then click "Download PDF" to save the file.'
            ],
            tip: 'The transcript counts faculty activities that were not cancelled and external activities that were approved.'
          },
          {
            heading: 'Thai version vs English version',
            groups: [
              {
                label: '',
                items: [
                  { term: 'Thai', text: 'The whole document is in Thai. Dates and academic years use the Buddhist Era (B.E.).' },
                  { term: 'English', text: 'The whole document is in English, including major names, activity types and skills. Dates and academic years use the Common Era (A.D.). Suits job or scholarship applications abroad.' }
                ]
              }
            ],
            tip: 'In both languages, your name and activity names appear exactly as recorded in the system (they are not translated automatically).'
          }
        ]
      }
    }
  },
  adminGuide: {
    title: 'User Guide',
    subtitle: 'How to manage student activities and skills as an admin. Choose a topic below to see the details.',
    guideFor: 'Guide for:',
    roleCentral: 'Central admin',
    roleBranch: 'Branch admin, {major}',
    centralOnlyBadge: 'Central admin only',
    jumpTo: 'Jump to',
    expandAll: 'Expand all',
    collapseAll: 'Collapse all',
    openPage: 'Open page',
    tip: 'Tip',
    sections: {
      dashboard: {
        title: 'Dashboard',
        summary: 'An overview of activities, participants and skills',
        topics: [
          {
            heading: 'Reading the overview statistics',
            groups: [
              {
                label: '',
                items: [
                  { term: 'Activities', text: 'Faculty activities in the selected period, excluding cancelled activities and student external activities.' },
                  { term: 'Students', text: 'All students in the system within your scope. Not affected by the period.' },
                  { term: 'Participants', text: 'Distinct students who took part as participants in activities in the selected period.' },
                  { term: 'Completion Rate', text: 'Completed activities ÷ activities that were not cancelled × 100. Activities past their end date count as completed.' }
                ]
              }
            ]
          },
          {
            heading: 'Using the year and semester filters',
            steps: [
              'Under "Dashboard History", choose the year (based on the year of each activity\'s start date).',
              'Choose the semester: All Semesters, Semester 1 (Jan–Jun) or Semester 2 (Jul–Dec).',
              'The stat cards, the growth chart and the skill distribution update straight away.'
            ]
          },
          {
            heading: 'Using the branch filter',
            audience: 'central',
            steps: [
              'Choose a branch from the "Branch" list to see only that branch, or "All Branches" for the whole faculty.',
              'The same branch filter is on the Activities, Student Skills and Approvals pages.'
            ]
          },
          {
            heading: 'What data you see',
            audience: 'branch',
            text: 'The dashboard shows only your branch automatically: activities your branch runs and students in your branch. Faculty-wide activities created by the central admin are not counted in the dashboard numbers.'
          },
          {
            heading: 'Reading the activity growth chart',
            steps: [
              'Each bar is the number of activities that started in that month (cancelled activities excluded).',
              'Switch between "MONTHLY" and "QUARTERLY" to change the grouping.',
              'Click a month or quarter label under the chart to narrow the stat cards and the skill distribution to that period.'
            ]
          },
          {
            heading: 'Reading the student skill distribution',
            steps: [
              'Switch between "PARTICIPANT" and "STAFF" to see the participant or organizer skill set.',
              'Each bar is the average skill level set on activities, shown as a percentage of level 5. The number in brackets is how many activities include that skill.',
              'The "AVG SCORE" ring is the average across every skill that has data.',
              'Use it to see which skills this period\'s activities focus on, and which skills have few activities.'
            ]
          }
        ]
      },
      activities: {
        title: 'Activities',
        summary: 'Create activities, manage participants, edit and cancel activities',
        topics: [
          {
            heading: 'Creating a new activity',
            steps: [
              'Click "Create New Activity" at the top right of the Activities page.',
              'Step 1: fill in the activity type, name, start and end dates, main responsible person and location (fields marked * are required). If you choose the "other" type, type it in. Click "Continue".',
              'Step 2: set the skill levels on both the "Staff" and "Participant" tabs. Every skill starts at level 3 and can be set from 1 to 5. Tick "Not related" for skills that do not apply.',
              'Click "Create Activity".'
            ],
            tip: 'Activities created by a branch admin belong to that branch. Activities created by the central admin are faculty-wide and visible to every branch.'
          },
          {
            heading: 'Adding students to an activity',
            steps: [
              'In the table, click "Manage" in the "MANAGE PARTICIPANTS" column of the activity.',
              'One at a time: choose "Add Student", search by student ID or name, choose the role "Participant" or "Organizer", and save.',
              'Many at once: choose "Import from File" and pick an .xlsx, .xls or .csv file.',
              'Click "Preview Import" and check the table (you can edit it there). Rows with issues are skipped.',
              'Click "Confirm Import".'
            ],
            tip: 'Students must already be in the system (the central admin imports them in Settings). An unknown student ID cannot be added.'
          },
          {
            heading: 'Downloading the import template',
            text: 'In the "Import from File" window, click "Download Template". The Excel file has the columns รหัสนักศึกษา (student ID), ชื่อ (first name), นามสกุล (last name), อีเมล (email) and สาขาวิชา (major), with 2 example rows. Delete the examples and fill in your data. To set roles, add a Role column (participant / organizer); without it everyone is a participant.'
          },
          {
            heading: 'Managing participants (edit, remove)',
            steps: [
              'Click "View Detail" on the activity to open its participant list.',
              'Click "Edit" on a student\'s row to change the first or last name, faculty, major or role (the student ID cannot be changed), then click "Save".',
              'Click "Remove" and confirm to take the student out of this activity (the student\'s record stays in the system).'
            ]
          },
          {
            heading: 'Editing and cancelling an activity',
            steps: [
              'In the table, click "Manage" in the "MANAGE ACTIVITY" column.',
              '"Edit Activity": change the details, status and skill levels, then click "Save Changes".',
              '"Mark as Completed" when the activity is over ("Reopen Activity" undoes it).',
              '"Cancel Activity": takes effect immediately, without a confirmation. Cancelled activities do not count towards students\' skills or transcripts.',
              '"Delete Activity": asks for confirmation first, then deletes permanently.'
            ],
            tip: 'If you cancel by mistake, change the status back in "Edit Activity". To keep the history, cancel instead of deleting.'
          },
          {
            heading: 'Searching and sorting activities',
            steps: [
              'Type in "SEARCH ACTIVITY" or the quick search box above the table (matches activity names and organizers).',
              'Use "CATEGORY" or "DATE FROM" to filter.',
              'Switch the order between "Sort by latest" and "Sort by start date", and click the arrow to flip oldest/newest.'
            ]
          },
          {
            heading: 'Using the branch filter on the Activities page',
            audience: 'central',
            text: 'Choose a branch from the "Branch" list to see that branch\'s activities (faculty-wide activities always show too), or "All Branches" to see everything.'
          }
        ]
      },
      skills: {
        title: 'Student Skills',
        summary: 'Skill overview, individual skills and comparison with the benchmark',
        topics: [
          {
            heading: 'Viewing the students\' skill overview',
            steps: [
              'The "AVERAGE SKILL SCORE" and "STUDENTS EVALUATED" cards at the top summarize the overview.',
              'Use the "Skill set" (participant / staff), "Class year" and "Major" filters to focus on a group. Click "Clear" to see everyone again.',
              'The "TOP AREA" and "GROWTH AREA" panels show the highest and lowest skills, with an action plan.'
            ],
            tip: 'Skill scores come from faculty activities and approved external activities.'
          },
          {
            heading: 'Viewing an individual student\'s skills',
            steps: [
              'Scroll to the "Individual Skills" table and search by student ID or name.',
              'Click "Filter Students" to filter by primary skill or score range.',
              'Click "View Radar" to open that student\'s skill proficiency analysis.',
              'In that window, use "Compare with" Major / Faculty / External to compare with the group average, and read the skill gap analysis with its recommendation.'
            ]
          },
          {
            heading: 'Viewing a student\'s activity history',
            text: 'In the "Individual Skills" table, click "View Activities" to see every activity of the student, with the type (Faculty Activity / External Activity), date, role and status.'
          },
          {
            heading: 'Reading the radar chart and the benchmark',
            steps: [
              'Choose the year and period (All Year / Semester 1 / Semester 2) above the chart.',
              'Choose the "View": Overall, By class year, By major, or By major × class year (up to 3 groups overlaid).',
              'The "Actual Proficiency" line is the students\' average score. The "Benchmark Level" line is the faculty target (4.0 by default).',
              'Skills where the actual line is inside the benchmark need more activities. Click "Show numbers for each group" to see the values.'
            ]
          },
          {
            heading: 'Setting the benchmark level',
            audience: 'central',
            steps: [
              'Click the "Benchmark" button on the radar chart.',
              'Set a value from 1.0 to 5.0 for each skill (participant and staff skill sets are set separately).',
              'Click "Save Benchmark". The values apply to every branch in the faculty.'
            ]
          },
          {
            heading: 'Using the branch filter',
            audience: 'central',
            text: 'Choose a branch from the "Branch" list at the top to limit the cards, chart and skill table to students in that branch.'
          }
        ]
      },
      approvals: {
        title: 'Approvals',
        summary: 'Review and approve external activities submitted by students',
        topics: [
          {
            heading: 'Viewing pending requests',
            steps: [
              'The cards at the top show Total Pending, Approved Today and Rejected Today.',
              'The "Pending" tab lists requests that have not been reviewed yet.',
              'Click "Filter" to choose a type (Skill Validation / Special Request / External Activity) and "Sort" to switch newest/oldest.'
            ]
          },
          {
            heading: 'Viewing request details',
            steps: [
              'Click "View Detail" on a request.',
              'Check the student, activity name, organizer, category, role, date and location.',
              'Look at the "Evidence" (click an image or file to open it) and "Skill Mapping (by student)", the skill levels the student rated themselves.'
            ]
          },
          {
            heading: 'Approving an external activity',
            steps: [
              'Click "Approve". The "Confirm Approval" window shows the skill levels the student chose.',
              'Click "Confirm Approve", then "OK" in the success window.',
              'The activity counts towards the student\'s skills and transcript straight away.'
            ],
            tip: 'Admins cannot change the skill levels. If they are not right, reject with a reason; the student can fix them and resubmit.'
          },
          {
            heading: 'Rejecting with a reason',
            steps: [
              'Click "Reject".',
              'Type the reason in "Comment / Reason for rejection" (required).',
              'Click "Confirm Reject". The student gets a notification with your reason.'
            ],
            tip: 'Say exactly what needs fixing, for example "The evidence does not show the activity name. Please attach the certificate."'
          },
          {
            heading: 'Viewing rejected requests',
            text: 'Open the "Rejected" tab to see rejected requests and their reasons. When a student edits and resubmits, the request moves back to "Pending" and you get a notification. (Approved requests are not listed on this page.)'
          },
          {
            heading: 'Using the branch filter',
            audience: 'central',
            text: 'Choose a branch from the "Branch" list to see only requests from students in that branch. Requests from students without a major are visible only to the central admin.'
          }
        ]
      },
      settings: {
        title: 'Settings',
        summary: 'Manage students, branch admins (central admin) and the transcript header',
        topics: [
          {
            heading: 'What branch admins can do in Settings',
            audience: 'branch',
            text: 'You can import, view and delete students in your own major only (rows with an empty major are set to your major automatically; rows for other majors are not imported). You can edit the transcript header like the central admin, and it applies to every major. Only the central admin can add or remove admins.'
          },
          {
            heading: 'Importing students into the system',
            steps: [
              'Under "Manage Students", click "Manage".',
              'Click "Choose file". .xlsx, .xls and .csv up to 5MB are supported (CSV can be UTF-8 or Windows-874).',
              'Review the table before importing: "New" rows are imported, "Duplicate (skipped)" are IDs already in the system, "Invalid" rows have errors.',
              'Click "Confirm Import", then check the summary and any rows not imported.'
            ],
            tip: 'Fill in every student\'s major. Branch admins cannot see students without a major.'
          },
          {
            heading: 'Downloading the Excel template',
            text: 'In the student import area, click "Download Template". The Excel file has the headers รหัสนักศึกษา, ชื่อ, นามสกุล, อีเมล and สาขาวิชา (student ID, first name, last name, email, major). Every cell is formatted as text, so leading zeros in student IDs are kept.'
          },
          {
            heading: 'Viewing and deleting student data',
            steps: [
              '"All Students" shows the 5 newest. Click "View all" to see everyone and search by ID, name, email or major.',
              'Click the trash icon on a row to delete that student (their activity memberships, external activities and evidence files are deleted too).',
              'Click "Delete all" and type DELETE to remove every student (faculty activities are kept).'
            ],
            tip: 'Deleting cannot be undone. Double-check before confirming.'
          },
          {
            heading: 'Adding a new branch admin',
            audience: 'central',
            steps: [
              'Under "Manage Admins", click "Manage", then "Add admin".',
              'Enter the email, choose the branch, and click "Save".',
              'The new admin signs in on the login page with that email and the default password 1234.'
            ],
            tip: 'The email must not belong to an existing admin or student.'
          },
          {
            heading: 'Removing a branch admin',
            audience: 'central',
            text: 'In the branch admin table, click the trash icon and confirm. That account is signed out immediately. You cannot delete your own account or the central admin.'
          },
          {
            heading: 'Editing the transcript header',
            steps: [
              'Under "Manage Transcript", click "Manage".',
              'Edit the university name, faculty name, document title, signatory name and signatory position in Thai and English. Empty fields use the defaults.',
              'Check the "Transcript preview" below; you can switch Style A / B and the language. It updates when you stop typing.',
              'Click "Save". New values apply to every PDF students generate from now on. "Use defaults" restores the original text.'
            ]
          }
        ]
      },
      notifications: {
        title: 'Notifications',
        summary: 'Know when students submit external activity requests',
        topics: [
          {
            heading: 'Viewing notifications from the bell',
            steps: [
              'The bell icon is at the top right of every page. The red number is how many are unread.',
              'Click the bell to open the 30 latest notifications (unread ones have a blue dot).',
              'Click a notification to open the Approvals page with that request\'s details.',
              'Click "Mark all as read" to clear the count.'
            ],
            tip: 'New notifications are checked every 30 seconds. Read status is tracked separately for each admin account.'
          },
          {
            heading: 'Types of notifications',
            groups: [
              {
                label: '',
                items: [
                  { term: 'New external activity request', text: 'A student submitted an external activity for review (blue icon).' },
                  { term: 'Edited and resubmitted', text: 'A student fixed a rejected external activity and sent it again (orange icon).' }
                ]
              }
            ]
          },
          {
            heading: 'The central admin receives notifications from every branch',
            audience: 'central',
            text: 'You see notifications from students in every branch, including students without a major. Branch admins see the same notifications, but only for their own branch.'
          },
          {
            heading: 'Notifications for your branch only',
            audience: 'branch',
            text: 'You only receive notifications for requests from students in your branch. Requests from other branches, or from students without a major, go to that branch\'s admin and the central admin.'
          }
        ]
      }
    }
  },
}
