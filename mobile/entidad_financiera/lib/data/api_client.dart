import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ApiClient {
  ApiClient._();
  static final ApiClient I = ApiClient._();

  final Dio dio = Dio(
    BaseOptions(
      baseUrl: const String.fromEnvironment(
        'API_BASE_URL',
        defaultValue:
            'http://10.0.2.2:8000', // emulador; en físico usa adb reverse y localhost
      ),
      headers: {'Accept': 'application/json'},
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 15),
    ),
  );

  final _storage = const FlutterSecureStorage();

  Future<void> init() async {
    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (opt, handler) async {
          final access = await _storage.read(key: 'access_token');
          if (access != null) {
            opt.headers['Authorization'] = 'Bearer $access';
          }
          handler.next(opt);
        },
        onError: (e, handler) async {
          if (e.response?.statusCode == 401) {
            final ok = await _refresh();
            if (ok) {
              final req = e.requestOptions;
              final access = await _storage.read(key: 'access_token');
              if (access != null)
                req.headers['Authorization'] = 'Bearer $access';
              final clone = await dio.fetch(req);
              return handler.resolve(clone);
            }
          }
          handler.next(e);
        },
      ),
    );
  }

  Future<bool> _refresh() async {
    final refresh = await _storage.read(key: 'refresh_token');
    if (refresh == null) return false;
    try {
      final res = await dio.post(
        '/api/auth/refresh/',
        data: {'refresh': refresh},
      );
      await _storage.write(
        key: 'access_token',
        value: res.data['access'] as String,
      );
      return true;
    } catch (_) {
      await _storage.deleteAll();
      return false;
    }
  }
}
