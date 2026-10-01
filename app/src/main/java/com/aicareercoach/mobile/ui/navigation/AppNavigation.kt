package com.aicareercoach.mobile.ui.navigation

import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Chat
import androidx.compose.material.icons.filled.Group
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Insights
import androidx.compose.material.icons.filled.MenuBook
import androidx.compose.material.icons.filled.Person
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.navigation.NavDestination.Companion.hierarchy
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.aicareercoach.mobile.data.CareerResource
import com.aicareercoach.mobile.data.AdminOverview
import com.aicareercoach.mobile.data.StudentAccount
import com.aicareercoach.mobile.data.UserSession
import com.aicareercoach.mobile.data.network.ApiClient
import com.aicareercoach.mobile.ui.screens.admin.AdminAnalyticsScreen
import com.aicareercoach.mobile.ui.screens.admin.AdminDashboardScreen
import com.aicareercoach.mobile.ui.screens.admin.AdminResourcesScreen
import com.aicareercoach.mobile.ui.screens.admin.AdminUploadScreen
import com.aicareercoach.mobile.ui.screens.admin.AdminUsersScreen
import com.aicareercoach.mobile.ui.screens.auth.ForgotPasswordScreen
import com.aicareercoach.mobile.ui.screens.auth.LandingScreen
import com.aicareercoach.mobile.ui.screens.auth.LoginRegisterScreen
import com.aicareercoach.mobile.ui.screens.shared.SimpleInfoScreen
import com.aicareercoach.mobile.ui.screens.student.AICareerChatScreen
import com.aicareercoach.mobile.ui.screens.student.CareerResourcesScreen
import com.aicareercoach.mobile.ui.screens.student.CareerAssessmentScreen
import com.aicareercoach.mobile.ui.screens.student.EditProfileScreen
import com.aicareercoach.mobile.ui.screens.student.FeedbackScreen
import com.aicareercoach.mobile.ui.screens.student.ResourceDetailScreen
import com.aicareercoach.mobile.ui.screens.student.StudentDashboardScreen
import com.aicareercoach.mobile.ui.screens.student.StudentProfileScreen

object Routes {
    const val Landing = "landing"
    const val Auth = "auth"
    const val ForgotPassword = "forgot"
    const val Student = "student"
    const val Dashboard = "dashboard"
    const val Chat = "chat"
    const val Resources = "resources"
    const val CareerAssessment = "careerAssessment"
    const val ResourceDetail = "resourceDetail/{id}"
    const val Profile = "profile"
    const val EditProfile = "editProfile"
    const val Help = "help"
    const val Privacy = "privacy"
    const val Feedback = "feedback"
    const val Admin = "admin"
    const val AdminHome = "adminHome"
    const val AdminResources = "adminResources"
    const val AdminUsers = "adminUsers"
    const val AdminAnalytics = "adminAnalytics"
    const val AdminUpload = "adminUpload"

    fun resourceDetail(id: String) = "resourceDetail/$id"
}

private data class TabItem(val route: String, val label: String, val icon: ImageVector)

private val studentTabs = listOf(
    TabItem(Routes.Dashboard, "Home", Icons.Default.Home),
    TabItem(Routes.Chat, "Coach", Icons.Default.Chat),
    TabItem(Routes.Resources, "Resources", Icons.Default.MenuBook),
    TabItem(Routes.Profile, "Profile", Icons.Default.Person),
)

private val adminTabs = listOf(
    TabItem(Routes.AdminHome, "Overview", Icons.Default.Home),
    TabItem(Routes.AdminResources, "Knowledge", Icons.Default.MenuBook),
    TabItem(Routes.AdminUsers, "Students", Icons.Default.Group),
    TabItem(Routes.AdminAnalytics, "Insights", Icons.Default.Insights),
)

@Composable
fun AppNavigation(
    modifier: Modifier = Modifier,
    navController: NavHostController = rememberNavController()
) {
    var session by remember { mutableStateOf<UserSession?>(null) }
    val resources = remember { mutableStateListOf<CareerResource>() }

    LaunchedEffect(session?.token) {
        resources.clear()
        val token = session?.token
        if (!token.isNullOrBlank()) ApiClient.getResources(token)?.let(resources::addAll)
    }

    fun goHome(destination: String) {
        navController.navigate(destination) {
            popUpTo(Routes.Landing) { inclusive = true }
            launchSingleTop = true
        }
    }

    fun logOut(from: String) {
        session = null
        resources.clear()
        navController.navigate(Routes.Landing) {
            popUpTo(from) { inclusive = true }
            launchSingleTop = true
        }
    }

    NavHost(
        navController = navController,
        startDestination = Routes.Landing,
        modifier = modifier
    ) {
        composable(Routes.Landing) {
            LandingScreen(
                onGetStarted = { navController.navigate("${Routes.Auth}?register=true") },
                onLogIn = { navController.navigate("${Routes.Auth}?register=false") }
            )
        }

        composable(
            route = "${Routes.Auth}?register={register}",
            arguments = listOf(
                navArgument("register") {
                    type = NavType.BoolType
                    defaultValue = false
                }
            )
        ) { entry ->
            LoginRegisterScreen(
                startInRegister = entry.arguments?.getBoolean("register") == true,
                onBack = { navController.popBackStack() },
                onForgotPassword = { navController.navigate(Routes.ForgotPassword) },
                onAuthenticated = { next ->
                    session = next
                    goHome(if (next.isAdmin) Routes.Admin else Routes.Student)
                }
            )
        }

        composable(Routes.ForgotPassword) {
            ForgotPasswordScreen(
                onBack = { navController.popBackStack() },
                onSent = { navController.popBackStack() }
            )
        }

        composable(Routes.Student) {
            val current = session
            if (current != null) StudentHome(
                session = current,
                resources = resources,
                onSessionChange = { session = it },
                onOpenFeedback = { navController.navigate(Routes.Feedback) },
                onLogOut = { logOut(Routes.Student) }
            ) else LandingScreen(
                onGetStarted = { navController.navigate("${Routes.Auth}?register=true") },
                onLogIn = { navController.navigate("${Routes.Auth}?register=false") }
            )
        }

        composable(Routes.Feedback) {
            FeedbackScreen(
                sessionToken = session?.token.orEmpty(),
                onBack = { navController.popBackStack() },
                onSubmit = { navController.popBackStack() }
            )
        }

        composable(Routes.Admin) {
            val current = session
            if (current != null && current.isAdmin) AdminHome(
                token = current.token,
                resources = resources,
                onResourceAdded = { resources.add(0, it) },
                onLogOut = { logOut(Routes.Admin) }
            ) else LandingScreen(
                onGetStarted = { navController.navigate("${Routes.Auth}?register=true") },
                onLogIn = { navController.navigate("${Routes.Auth}?register=false") }
            )
        }
    }
}

@Composable
private fun StudentHome(
    session: UserSession,
    resources: List<CareerResource>,
    onSessionChange: (UserSession) -> Unit,
    onOpenFeedback: () -> Unit,
    onLogOut: () -> Unit
) {
    val tabNav = rememberNavController()
    val backStack by tabNav.currentBackStackEntryAsState()
    val currentRoute = backStack?.destination?.route
    val showBar = studentTabs.any { it.route == currentRoute }
    var chatSeed by remember { mutableStateOf<String?>(null) }

    Scaffold(
        bottomBar = {
            if (showBar) {
                NavigationBar(windowInsets = WindowInsets(0, 0, 0, 0)) {
                    studentTabs.forEach { tab ->
                        val selected = backStack?.destination?.hierarchy?.any { it.route == tab.route } == true
                        NavigationBarItem(
                            selected = selected,
                            onClick = { tabNav.navigateToTab(tab.route) },
                            icon = { Icon(tab.icon, contentDescription = tab.label) },
                            label = { Text(tab.label) }
                        )
                    }
                }
            }
        }
    ) { innerPadding ->
        NavHost(
            navController = tabNav,
            startDestination = Routes.Dashboard,
            modifier = Modifier.padding(innerPadding)
        ) {
            composable(Routes.Dashboard) {
                StudentDashboardScreen(
                    session = session,
                    onOpenChat = { tabNav.navigateToTab(Routes.Chat) },
                    onOpenResources = { tabNav.navigateToTab(Routes.Resources) },
                    onOpenProfile = { tabNav.navigateToTab(Routes.Profile) },
                    onReviewCv = {
                        chatSeed = "How can I improve my CV for internship applications?"
                        tabNav.navigateToTab(Routes.Chat)
                    },
                    onInterviewPrep = {
                        chatSeed = "Help me with interview prep"
                        tabNav.navigateToTab(Routes.Chat)
                    },
                    onExploreCareers = { tabNav.navigate(Routes.CareerAssessment) }
                )
            }
            composable(Routes.Chat) {
                AICareerChatScreen(
                    session = session,
                    seedQuestion = chatSeed,
                    onSeedConsumed = { chatSeed = null }
                )
            }
            composable(Routes.CareerAssessment) {
                CareerAssessmentScreen(session = session, onBack = { tabNav.popBackStack() })
            }
            composable(Routes.Resources) {
                CareerResourcesScreen(
                    resources = resources,
                    onOpenResource = { tabNav.navigate(Routes.resourceDetail(it.id)) }
                )
            }
            composable(
                route = Routes.ResourceDetail,
                arguments = listOf(navArgument("id") { type = NavType.StringType })
            ) { entry ->
                val id = entry.arguments?.getString("id")
                val resource = resources.find { it.id == id }
                if (resource != null) ResourceDetailScreen(
                    resource = resource,
                    onBack = { tabNav.popBackStack() },
                    onAskCoach = {
                        chatSeed = "Tell me about ${resource.title}"
                        tabNav.navigateToTab(Routes.Chat)
                    }
                ) else SimpleInfoScreen(
                    title = "Resource unavailable",
                    body = "This resource could not be loaded. Check your connection and try again.",
                    onBack = { tabNav.popBackStack() }
                )
            }
            composable(Routes.Profile) {
                StudentProfileScreen(
                    session = session,
                    onEditProfile = { tabNav.navigate(Routes.EditProfile) },
                    onOpenChat = { tabNav.navigateToTab(Routes.Chat) },
                    onOpenResources = { tabNav.navigateToTab(Routes.Resources) },
                    onOpenFeedback = onOpenFeedback,
                    onOpenHelp = { tabNav.navigate(Routes.Help) },
                    onOpenPrivacy = { tabNav.navigate(Routes.Privacy) },
                    onLogOut = onLogOut
                )
            }
            composable(Routes.EditProfile) {
                EditProfileScreen(
                    session = session,
                    onBack = { tabNav.popBackStack() },
                    onSave = {
                        onSessionChange(it)
                        tabNav.popBackStack()
                    }
                )
            }
            composable(Routes.Help) {
                SimpleInfoScreen(
                    title = "Help & Support",
                    body = "Ask the coach from the Coach tab, browse Career Resources, or send feedback on an answer from Profile. Password recovery is not available yet; contact your administrator for help.",
                    onBack = { tabNav.popBackStack() }
                )
            }
            composable(Routes.Privacy) {
                SimpleInfoScreen(
                    title = "Privacy Policy",
                    body = "Your account, chat history, career assessments, and feedback are stored by the career coach backend. Use your own account and do not share your password.",
                    onBack = { tabNav.popBackStack() }
                )
            }
        }
    }
}

@Composable
private fun AdminHome(
    token: String,
    resources: List<CareerResource>,
    onResourceAdded: (CareerResource) -> Unit,
    onLogOut: () -> Unit
) {
    var overview by remember { mutableStateOf<AdminOverview?>(null) }
    val students = remember { mutableStateListOf<StudentAccount>() }
    LaunchedEffect(token) {
        overview = ApiClient.getAdminOverview(token)
        students.clear()
        ApiClient.getAdminStudents(token)?.let(students::addAll)
    }
    val tabNav = rememberNavController()
    val backStack by tabNav.currentBackStackEntryAsState()
    val currentRoute = backStack?.destination?.route
    val showBar = adminTabs.any { it.route == currentRoute }

    Scaffold(
        bottomBar = {
            if (showBar) {
                NavigationBar(windowInsets = WindowInsets(0, 0, 0, 0)) {
                    adminTabs.forEach { tab ->
                        val selected = backStack?.destination?.hierarchy?.any { it.route == tab.route } == true
                        NavigationBarItem(
                            selected = selected,
                            onClick = { tabNav.navigateToTab(tab.route) },
                            icon = { Icon(tab.icon, contentDescription = tab.label) },
                            label = { Text(tab.label) }
                        )
                    }
                }
            }
        }
    ) { innerPadding ->
        NavHost(
            navController = tabNav,
            startDestination = Routes.AdminHome,
            modifier = Modifier.padding(innerPadding)
        ) {
            composable(Routes.AdminHome) {
                AdminDashboardScreen(
                    overview = overview,
                    onOpenResources = { tabNav.navigateToTab(Routes.AdminResources) },
                    onOpenUsers = { tabNav.navigateToTab(Routes.AdminUsers) },
                    onOpenAnalytics = { tabNav.navigateToTab(Routes.AdminAnalytics) },
                    onUploadResource = { tabNav.navigate(Routes.AdminUpload) },
                    onLogOut = onLogOut
                )
            }
            composable(Routes.AdminResources) {
                AdminResourcesScreen(
                    resources = resources,
                    onUpload = { tabNav.navigate(Routes.AdminUpload) }
                )
            }
            composable(Routes.AdminUsers) {
                AdminUsersScreen(students = students)
            }
            composable(Routes.AdminAnalytics) {
                AdminAnalyticsScreen(overview = overview)
            }
            composable(Routes.AdminUpload) {
                AdminUploadScreen(
                    token = token,
                    onBack = { tabNav.popBackStack() },
                    onUploaded = {
                        onResourceAdded(it)
                        tabNav.popBackStack()
                    }
                )
            }
        }
    }
}

private fun NavHostController.navigateToTab(route: String) {
    navigate(route) {
        popUpTo(graph.findStartDestination().id) { saveState = true }
        launchSingleTop = true
        restoreState = true
    }
}
