// lib/features/home/home_screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme.dart';
import '../auth/auth_controller.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authProvider).user;
    final nombre = (user?['first_name'] as String?)?.trim();
    final saludo =
        (nombre?.isNotEmpty ?? false) ? nombre! : (user?['username'] ?? '');

    return Scaffold(
      appBar: AppBar(
        title: const Text('Mi Crédito'),
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
          Text('Hola, $saludo',
              style:
                  const TextStyle(fontSize: 22, fontWeight: FontWeight.w800)),

          const SizedBox(height: 16),

          // Accesos rápidos en grid
          GridView(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 2, // 2 por fila
              crossAxisSpacing: 12,
              mainAxisSpacing: 12,
              childAspectRatio: 1.35,
            ),
            children: [
              _QuickAction(
                icon: Icons.add_circle_outline,
                label: 'Nueva solicitud',
                onTap: () => context.go('/solicitudes/new'),
              ),
              _QuickAction(
                icon: Icons.description_outlined,
                label: 'Mis solicitudes',
                onTap: () => context.go('/solicitudes'),
              ),
              _QuickAction(
                icon: Icons.person_outline,
                label: 'Mi perfil',
                onTap: () => context.go('/profile'),
              ),
              _QuickAction(
                icon: Icons.notifications_outlined,
                label: 'Notificaciones',
                onTap: () => context.go('/notifications'),
              ),
            ],
          ),

          const SizedBox(height: 24),

          // Tips
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(14),
              boxShadow: const [
                BoxShadow(
                    color: Colors.black12, blurRadius: 8, offset: Offset(0, 2))
              ],
            ),
            child: const Text(
              'Puedes crear una solicitud y hacer seguimiento del estado. '
              'Cuando sea APROBADA, verás tu plan de pagos.',
            ),
          ),
        ],
      ),
    );
  }
}

class _QuickAction extends StatelessWidget {
  const _QuickAction({required this.icon, required this.label, this.onTap});
  final IconData icon;
  final String label;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          boxShadow: const [
            BoxShadow(
                color: Colors.black12, blurRadius: 10, offset: Offset(0, 2)),
          ],
        ),
        padding: const EdgeInsets.all(16),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 28),
            const SizedBox(height: 10),
            Text(label,
                textAlign: TextAlign.center,
                style: TextStyle(
                    color: AppColors.muted, fontWeight: FontWeight.w600)),
          ],
        ),
      ),
    );
  }
}
