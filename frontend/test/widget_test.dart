import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tarot_app/main.dart';

void main() {
  testWidgets('Application démarre correctement', (WidgetTester tester) async {
    // Construire notre application et déclencher un frame.
    await tester.pumpWidget(const TarotApp());

    // Vérifier que nous trouvons au moins un widget contenant 'Tarot App'
    expect(find.textContaining('Tarot'), findsOneWidget);
  });
}