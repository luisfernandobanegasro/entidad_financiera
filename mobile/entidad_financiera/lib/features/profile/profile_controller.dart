import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/profile_repository.dart';
import '../auth/auth.dart';

class ProfileState {
  final bool loading;
  final Map<String, dynamic>? me; // mismo shape de /me/
  final String? error;
  const ProfileState({this.loading = false, this.me, this.error});
  ProfileState copyWith(
          {bool? loading, Map<String, dynamic>? me, String? error}) =>
      ProfileState(
          loading: loading ?? this.loading, me: me ?? this.me, error: error);
}

class ProfileController extends StateNotifier<ProfileState> {
  ProfileController(this._repo, this._ref) : super(const ProfileState());
  final ProfileRepository _repo;
  final Ref _ref;

  Future<void> load() async {
    state = state.copyWith(loading: true, error: null);
    try {
      final me = await _repo.me();
      state = state.copyWith(loading: false, me: me);
    } catch (e) {
      state = state.copyWith(loading: false, error: e.toString());
    }
  }

  Future<void> saveCliente(Map<String, dynamic> data) async {
    final clienteId = (_ref.read(authProvider).user?['cliente_id']) as int?;
    if (clienteId == null) throw Exception('No se encontró cliente_id.');
    state = state.copyWith(loading: true, error: null);
    try {
      await _repo.updateCliente(clienteId: clienteId, data: data);
      await load(); // refresca /me/
    } catch (e) {
      state = state.copyWith(loading: false, error: e.toString());
      rethrow;
    }
  }
}

final profileRepoProvider = Provider((_) => ProfileRepository());
final profileProvider =
    StateNotifierProvider<ProfileController, ProfileState>((ref) {
  return ProfileController(ref.read(profileRepoProvider), ref);
});
