import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend_flutter/screens/home_screen.dart';
import 'package:frontend_flutter/screens/projects_screen.dart';
import 'package:frontend_flutter/screens/settings_screen.dart';
import 'package:frontend_flutter/screens/tasks_screen.dart';
import 'package:frontend_flutter/services/api_service.dart';
import 'package:frontend_flutter/models/project.dart';
import 'package:frontend_flutter/models/session.dart';
import 'package:frontend_flutter/models/task.dart';
import 'package:frontend_flutter/i18n/language_controller.dart';

class MockApiService extends ApiService {
  @override
  Future<Map<String, dynamic>> getStatus() async {
    return {
      'status': 'online',
      'active_project': {'name': 'Demo Project'},
      'active_session': {'title': 'Main Chat'},
      'confirm_mode': false,
      'model': 'gemini-3.7-flash',
      'active_tasks_count': 1,
    };
  }

  @override
  Future<List<Project>> getProjects() async {
    return [
      Project(id: 1, name: 'Project Alpha', path: '/path/alpha', isActive: true),
      Project(id: 2, name: 'Project Beta', path: '/path/beta', isActive: false),
    ];
  }

  @override
  Future<List<Session>> getSessions({int? projectId}) async {
    return [
      Session(
        id: 1,
        projectId: 1,
        title: 'Session Alpha',
        conversationId: 'uuid-1',
        isActive: true,
      ),
    ];
  }

  @override
  Future<List<ScheduledTask>> getTasks() async {
    return [
      ScheduledTask(
        id: 1,
        title: 'Morning Report',
        cronExpression: '0 9 * * *',
        prompt: 'Check logs',
        isActive: true,
      ),
    ];
  }

  @override
  Future<Map<String, dynamic>> getSettings() async {
    return {
      'confirm_mode': false,
      'model': 'gemini-3.7-flash',
      'language': 'ru',
    };
  }

  @override
  Future<Map<String, dynamic>> getModels() async {
    return {
      'models': [
        {'id': '', 'name': '⚡ По умолчанию', 'description': 'Auto'},
        {'id': 'gemini-3.7-flash', 'name': 'Gemini 3.7 Flash', 'description': 'High reasoning'},
      ],
      'current_model': 'gemini-3.7-flash',
    };
  }
}

void main() {
  setUp(() {
    LanguageController.instance.setLanguage('ru');
  });

  testWidgets('HomeScreen renders tabs and responds to tap', (WidgetTester tester) async {
    final mockApi = MockApiService();

    await tester.pumpWidget(
      MaterialApp(
        home: HomeScreen(api: mockApi),
      ),
    );

    await tester.pumpAndSettle();

    // Verify NavigationBar exists
    expect(find.byType(NavigationBar), findsOneWidget);

    // Verify tabs are present
    expect(find.text('Проекты'), findsWidgets);
    expect(find.text('Беседы'), findsWidgets);
    expect(find.text('Задания'), findsWidgets);
    expect(find.text('Настройки'), findsWidgets);

    // Tap 'Настройки' (index 3)
    await tester.tap(find.text('Настройки'));
    await tester.pumpAndSettle();

    // Settings screen is now active
    expect(find.byType(SettingsScreen), findsOneWidget);
  });

  testWidgets('SettingsScreen displays language toggle and models', (WidgetTester tester) async {
    final mockApi = MockApiService();

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: SettingsScreen(api: mockApi),
        ),
      ),
    );

    await tester.pumpAndSettle();

    // Language options
    expect(find.text('🇷🇺 Русский (RU)'), findsOneWidget);
    expect(find.text('🇬🇧 English (EN)'), findsOneWidget);

    // AI model section
    expect(find.textContaining('Gemini 3.7 Flash'), findsOneWidget);

    // Safety section
    expect(find.byType(Switch), findsOneWidget);
  });

  testWidgets('ProjectsScreen displays projects list', (WidgetTester tester) async {
    final mockApi = MockApiService();

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: ProjectsScreen(
            api: mockApi,
            onProjectChanged: () {},
          ),
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Project Alpha'), findsOneWidget);
    expect(find.text('Project Beta'), findsOneWidget);
    expect(find.text('АКТИВНЫЙ'), findsOneWidget);
  });

  testWidgets('TasksScreen displays scheduled tasks list', (WidgetTester tester) async {
    final mockApi = MockApiService();

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: TasksScreen(apiService: mockApi),
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Morning Report'), findsOneWidget);
    expect(find.textContaining('0 9 * * *'), findsOneWidget);
  });
}
