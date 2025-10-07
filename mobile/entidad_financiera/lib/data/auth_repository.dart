// lib/data/auth_repository.dart
import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../data/api_client.dart';

class AuthRepository {
  final Dio _dio = ApiClient.I.dio;
  final _storage = const FlutterSecureStorage();

  static const _kAccess = 'access_token';
  static const _kRefresh = 'refresh_token';

  Future<void> login({
    required String username,
    required String password,
  }) async {
    final resp = await _dio.post('/api/auth/login/', data: {
      'username': username,
      'password': password,
    });

    // Log de ayuda
    // ignore: avoid_print
    print('[API] login resp: ${resp.data}');

    final data = resp.data as Map<String, dynamic>;
    final access =
        (data['access'] ?? data['access_token'] ?? data['token']) as String;
    final refresh = (data['refresh'] ?? data['refresh_token'] ?? '') as String?;

    await _storage.write(key: _kAccess, value: access);
    if (refresh != null && refresh.isNotEmpty) {
      await _storage.write(key: _kRefresh, value: refresh);
    }
    _dio.options.headers['Authorization'] = 'Bearer $access';
  }

  // ⬇️ DEVUELVE SIEMPRE UN MAP, aunque /api/users/ sea una lista
  Future<Map<String, dynamic>?> me() async {
    final resp = await _dio.get('/api/users/');
    // ignore: avoid_print
    print('[API] me() → status:${resp.statusCode} data:${resp.data}');

    final data = resp.data;
    if (data is Map<String, dynamic>) {
      return data;
    }
    if (data is List && data.isNotEmpty && data.first is Map<String, dynamic>) {
      // mientras no tengas /api/auth/me/, usa el primer usuario
      return data.first as Map<String, dynamic>;
    }
    return null;
  }

  Future<void> refresh() async {
    final refresh = await _storage.read(key: _kRefresh);
    if (refresh == null) return;
    final resp = await _dio.post(
      '/api/auth/refresh/',
      data: {'refresh': refresh},
    );
    final access = resp.data['access'] as String;
    await _storage.write(key: _kAccess, value: access);
    _dio.options.headers['Authorization'] = 'Bearer $access';
  }

  Future<void> register({
    required String username,
    required String email,
    required String password,
  }) async {
    await _dio.post(
      '/api/users/',
      data: {'username': username, 'email': email, 'password': password},
    );
  }

  Future<void> logout() async {
    await _storage.delete(key: _kAccess);
    await _storage.delete(key: _kRefresh);
    _dio.options.headers.remove('Authorization');
  }

  Future<bool> loadTokensIfAny() async {
    final access = await _storage.read(key: _kAccess);
    if (access == null) return false;
    _dio.options.headers['Authorization'] = 'Bearer $access';
    return true;
  }
}
