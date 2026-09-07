package com.aicareercoach.mobile.ui.navigation

import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Chat
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.MenuBook
import androidx.compose.material.icons.filled.Person
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
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
import com.aicareercoach.mobile.ui.screens.AICareerChatScreen
import com.aicareercoach.mobile.ui.screens.AdminDashboardScreen
import com.aicareercoach.mobile.ui.screens.CareerResourcesScreen
import com.aicareercoach.mobile.ui.screens.FeedbackScreen
import com.aicareercoach.mobile.ui.screens.LandingScreen
import com.aicareercoach.mobile.ui.screens.LoginRegisterScreen
import com.aicareercoach.mobile.ui.screens.StudentDashboardScreen
import com.aicareercoach.mobile.ui.screens.StudentProfileScreen

object Routes {
    const val Landing = "landing"
    const val Auth = "auth"
    const val Student = "student"
    const val Dashboard = "dashboard"
    const val Chat = "chat"
    const val Resources = "resources"
    const val Profile = "profile"
    const val Feedback = "feedback"
    const val Admin = "admin"
}

private data class StudentTab(
    val route: String,
    val label: String,
    val icon: ImageVector
)

private val studentTabs = listOf(
    StudentTab(Routes.Dashboard, "Home", Icons.Default.Home),
    StudentTab(Routes.Chat, "Coach", Icons.Default.Chat),
    StudentTab(Routes.Resources, "Resources", Icons.Default.MenuBook),
    StudentTab(Routes.Profile, "Profile", Icons.Default.Person),
)

@Composable
fun AppNavigation(
    modifier: Modifier = Modifier,
    navController: NavHostController = rememberNavController()
) {
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
            val startInRegister = entry.arguments?.getBoolean("register") == true
            LoginRegisterScreen(
                startInRegister = startInRegister,
                onBack = { navController.popBackStack() },
                onAuthenticated = { isAdmin ->
                    val destination = if (isAdmin) Routes.Admin else Routes.Student
                    navController.navigate(destination) {
                        popUpTo(Routes.Landing) { inclusive = true }
                        launchSingleTop = true
                    }
                }
            )
        }

        composable(Routes.Student) {
            StudentHome(
                onOpenFeedback = { navController.navigate(Routes.Feedback) },
                onLogOut = {
                    navController.navigate(Routes.Landing) {
                        popUpTo(Routes.Student) { inclusive = true }
                        launchSingleTop = true
                    }
                }
            )
        }

        composable(Routes.Feedback) {
            FeedbackScreen(
                onBack = { navController.popBackStack() },
                onSubmit = { navController.popBackStack() }
            )
        }

        composable(Routes.Admin) {
            AdminDashboardScreen(
                onLogOut = {
                    navController.navigate(Routes.Landing) {
                        popUpTo(Routes.Admin) { inclusive = true }
                        launchSingleTop = true
                    }
                }
            )
        }
    }
}

@Composable
private fun StudentHome(
    onOpenFeedback: () -> Unit,
    onLogOut: () -> Unit
) {
    val tabNav = rememberNavController()
    val backStack by tabNav.currentBackStackEntryAsState()
    val currentRoute = backStack?.destination

    Scaffold(
        bottomBar = {
            NavigationBar(windowInsets = WindowInsets(0, 0, 0, 0)) {
                studentTabs.forEach { tab ->
                    val selected = currentRoute?.hierarchy?.any { it.route == tab.route } == true
                    NavigationBarItem(
                        selected = selected,
                        onClick = {
                            tabNav.navigate(tab.route) {
                                popUpTo(tabNav.graph.findStartDestination().id) {
                                    saveState = true
                                }
                                launchSingleTop = true
                                restoreState = true
                            }
                        },
                        icon = { Icon(tab.icon, contentDescription = tab.label) },
                        label = { Text(tab.label) }
                    )
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
                    onOpenChat = { tabNav.navigateToTab(Routes.Chat) },
                    onOpenResources = { tabNav.navigateToTab(Routes.Resources) },
                    onOpenProfile = { tabNav.navigateToTab(Routes.Profile) },
                    onReviewCv = { tabNav.navigateToTab(Routes.Chat) },
                    onInterviewPrep = { tabNav.navigateToTab(Routes.Chat) }
                )
            }
            composable(Routes.Chat) {
                AICareerChatScreen()
            }
            composable(Routes.Resources) {
                CareerResourcesScreen(
                    onOpenChat = { tabNav.navigateToTab(Routes.Chat) }
                )
            }
            composable(Routes.Profile) {
                StudentProfileScreen(
                    onOpenChat = { tabNav.navigateToTab(Routes.Chat) },
                    onOpenResources = { tabNav.navigateToTab(Routes.Resources) },
                    onOpenFeedback = onOpenFeedback,
                    onLogOut = onLogOut
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
