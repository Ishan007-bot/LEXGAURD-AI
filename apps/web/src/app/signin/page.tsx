'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useAuth } from '@/lib/auth-context';

export default function SignInPage() {
  const { user, configured, signInWithGoogle } = useAuth();
  const router = useRouter();
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (user) router.replace('/analyze');
  }, [user, router]);

  const onSignIn = async () => {
    setError(null);
    try {
      await signInWithGoogle();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Sign-in failed.');
    }
  };

  return (
    <section className="container flex min-h-[80vh] items-center justify-center py-16">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Sign in to LexGuard</CardTitle>
          <CardDescription>
            One click with Google. We never store your contracts longer than your session unless
            you ask us to.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <Button onClick={() => void onSignIn()} disabled={!configured} size="lg">
            Continue with Google
          </Button>
          {!configured && (
            <p role="alert" className="text-sm text-muted-foreground">
              Firebase isn&apos;t configured for this build. Set the{' '}
              <code>NEXT_PUBLIC_FIREBASE_*</code> environment variables.
            </p>
          )}
          {error && (
            <p role="alert" className="text-sm text-destructive">
              {error}
            </p>
          )}
        </CardContent>
      </Card>
    </section>
  );
}
