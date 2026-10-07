import 'package:flutter_test/flutter_test.dart';
import 'package:frontend_flutter/i18n/language_controller.dart';
import 'package:frontend_flutter/i18n/app_strings.dart';

void main() {
  group('LanguageController Tests', () {
    test('Singleton initial state and language switching', () {
      final controller = LanguageController.instance;

      int notifyCount = 0;
      void listener() => notifyCount++;
      controller.addListener(listener);

      // Switch to English
      controller.setLanguage('en');
      expect(controller.currentLanguage, 'en');
      expect(controller.isRussian, isFalse);
      expect(notifyCount, 1);

      // Setting same language should not notify
      controller.setLanguage('en');
      expect(notifyCount, 1);

      // Setting invalid language should be ignored
      controller.setLanguage('de');
      expect(controller.currentLanguage, 'en');
      expect(notifyCount, 1);

      // Switch back to Russian
      controller.setLanguage('ru');
      expect(controller.currentLanguage, 'ru');
      expect(controller.isRussian, isTrue);
      expect(notifyCount, 2);

      controller.removeListener(listener);
    });
  });

  group('AppStrings / S.tr Tests', () {
    test('Translations in Russian and English', () {
      final controller = LanguageController.instance;

      controller.setLanguage('ru');
      expect(S.tr('app_title'), 'Gravigram Mini App');
      expect(S.tr('nav_projects'), 'Проекты');
      expect(S.tr('settings_title'), 'Настройки');

      controller.setLanguage('en');
      expect(S.tr('app_title'), 'Gravigram Mini App');
      expect(S.tr('nav_projects'), 'Projects');
      expect(S.tr('settings_title'), 'Settings');

      // Parameter interpolation
      expect(S.tr('task_started', params: {'id': '42'}), 'Task #42 started!');

      controller.setLanguage('ru');
      expect(S.tr('task_started', params: {'id': '42'}), 'Задание #42 запущено!');

      // Unknown key falls back to key name
      expect(S.tr('unknown_key_999'), 'unknown_key_999');
    });
  });
}
