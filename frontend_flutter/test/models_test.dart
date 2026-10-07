import 'package:flutter_test/flutter_test.dart';
import 'package:frontend_flutter/models/project.dart';
import 'package:frontend_flutter/models/session.dart';
import 'package:frontend_flutter/models/task.dart';

void main() {
  group('Project Model Tests', () {
    test('Project fromJson and toJson', () {
      final json = {
        'id': 1,
        'name': 'Test Project',
        'path': '/workspace/test',
        'is_active': 1,
        'created_at': '2026-10-07T12:00:00Z',
      };

      final project = Project.fromJson(json);
      expect(project.id, 1);
      expect(project.name, 'Test Project');
      expect(project.path, '/workspace/test');
      expect(project.isActive, isTrue);

      final outJson = project.toJson();
      expect(outJson['id'], 1);
      expect(outJson['name'], 'Test Project');
      expect(outJson['is_active'], 1);
    });
  });

  group('Session Model Tests', () {
    test('Session fromJson and toJson', () {
      final json = {
        'id': 42,
        'project_id': 1,
        'title': 'Debug Session',
        'conversation_id': 'conv-uuid-123',
        'is_active': 0,
        'created_at': '2026-10-07T10:00:00Z',
        'updated_at': '2026-10-07T11:00:00Z',
      };

      final session = Session.fromJson(json);
      expect(session.id, 42);
      expect(session.projectId, 1);
      expect(session.title, 'Debug Session');
      expect(session.conversationId, 'conv-uuid-123');
      expect(session.isActive, isFalse);

      final outJson = session.toJson();
      expect(outJson['title'], 'Debug Session');
      expect(outJson['is_active'], 0);
    });
  });

  group('ScheduledTask Model Tests', () {
    test('ScheduledTask fromJson with full fields', () {
      final json = {
        'id': 99,
        'title': 'Daily Audit',
        'cron_expression': '0 9 * * *',
        'prompt': 'Check system logs',
        'project_id': 2,
        'project_name': 'Server Alpha',
        'is_active': 1,
        'last_run_at': '2026-10-07 09:00:00',
        'next_run_at': '2026-10-08 09:00:00',
        'created_at': '2026-10-01 00:00:00',
      };

      final task = ScheduledTask.fromJson(json);
      expect(task.id, 99);
      expect(task.title, 'Daily Audit');
      expect(task.cronExpression, '0 9 * * *');
      expect(task.isActive, isTrue);
      expect(task.projectName, 'Server Alpha');
    });

    test('ScheduledTask fromJson with defaults', () {
      final json = {
        'id': 7,
        'is_active': false,
      };

      final task = ScheduledTask.fromJson(json);
      expect(task.id, 7);
      expect(task.title, 'Задание #7');
      expect(task.cronExpression, '');
      expect(task.isActive, isFalse);
    });
  });
}
