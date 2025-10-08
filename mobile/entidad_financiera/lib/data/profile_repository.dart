import 'api_client.dart';

class ProfileRepository {
  final _api = ApiClient.I;

  Future<Map<String, dynamic>> me() async {
    final resp = await _api.get('/me/');
    return (resp.data as List).first;
  }

  Future<Map<String, dynamic>> updateCliente({
    required int clienteId,
    required Map<String, dynamic> data,
  }) async {
    final resp = await _api.patch('/clientes/$clienteId/', data);
    return resp.data as Map<String, dynamic>;
  }
}
