import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme.dart';
import '../auth/auth_controller.dart';
import 'package:go_router/go_router.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(authProvider);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Home'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () async {
              await ref.read(authProvider.notifier).logout();
              if (context.mounted) context.go('/login');
            },
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(14),
              boxShadow: const [
                BoxShadow(
                  color: Colors.black12,
                  blurRadius: 8,
                  offset: Offset(0, 2),
                ),
              ],
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Solicitud de Crédito',
                  style: TextStyle(fontWeight: FontWeight.w700, fontSize: 16),
                ),
                const SizedBox(height: 6),
                Text('En revisión', style: TextStyle(color: AppColors.muted)),
              ],
            ),
          ),
          const SizedBox(height: 16),
          ListTile(
            leading: const CircleAvatar(child: Icon(Icons.add)),
            title: const Text('Nueva solicitud'),
            onTap: () {},
          ),
          ListTile(
            leading: const CircleAvatar(
              child: Icon(Icons.description_outlined),
            ),
            title: const Text('Mis solicitudes'),
            onTap: () {},
          ),
          ListTile(
            leading: const CircleAvatar(child: Icon(Icons.person_outline)),
            title: const Text('Mi perfil'),
            subtitle: Text(state.user?['email'] ?? ''),
            onTap: () {},
          ),
        ],
      ),
    );
  }
}
