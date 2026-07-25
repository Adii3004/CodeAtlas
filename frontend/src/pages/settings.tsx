import { useQueryClient } from "@tanstack/react-query";
import { Check, Plug, RotateCcw, Trash2 } from "lucide-react";
import { useState, type ReactNode } from "react";
import { toast } from "sonner";

import { ConfirmDialog } from "@/components/common/confirm-dialog";
import {
  PageContainer,
  PageHeader,
  SectionHeading,
} from "@/components/common/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { usePreferences } from "@/hooks/use-preferences";
import { useRepositories } from "@/hooks/use-repositories";
import { api } from "@/lib/api/endpoints";
import { env, getApiBaseUrl, STORAGE_KEYS } from "@/lib/env";
import { useTheme, type Theme } from "@/providers/theme-provider";

function SettingRow({
  label,
  description,
  htmlFor,
  control,
}: {
  label: string;
  description?: string;
  htmlFor?: string;
  control: ReactNode;
}) {
  return (
    <div className="flex items-start justify-between gap-6 py-4">
      <div className="min-w-0 space-y-1">
        <Label htmlFor={htmlFor}>{label}</Label>
        {description ? (
          <p className="text-muted-foreground text-xs leading-relaxed">
            {description}
          </p>
        ) : null}
      </div>
      <div className="flex w-40 shrink-0 justify-end">{control}</div>
    </div>
  );
}

export default function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const { preferences, update, reset } = usePreferences();
  const { repositories, clear } = useRepositories();
  const queryClient = useQueryClient();

  const [apiUrl, setApiUrl] = useState(getApiBaseUrl);
  const [testing, setTesting] = useState(false);
  const [clearOpen, setClearOpen] = useState(false);

  const saveApiUrl = async () => {
    const trimmed = apiUrl.trim().replace(/\/+$/, "");
    if (trimmed.length === 0) {
      window.localStorage.removeItem(STORAGE_KEYS.apiBaseUrl);
      setApiUrl(env.apiBaseUrl);
    } else {
      window.localStorage.setItem(STORAGE_KEYS.apiBaseUrl, trimmed);
    }
    await queryClient.invalidateQueries();
    toast.success("Connection updated", {
      description: `Now talking to ${trimmed || env.apiBaseUrl}.`,
    });
  };

  const testConnection = async () => {
    setTesting(true);
    try {
      const health = await api.health();
      toast.success("Backend is reachable", {
        description: `${health.app_name} v${health.version} responded.`,
      });
    } catch (error) {
      toast.error("Could not reach the backend", {
        description:
          error instanceof Error ? error.message : "Unknown error.",
      });
    } finally {
      setTesting(false);
    }
  };

  return (
    <PageContainer className="max-w-3xl space-y-8">
      <PageHeader
        eyebrow="Make it yours"
        title="Settings"
        description="Connection, appearance, and answer defaults. Everything here is stored in this browser only."
      />

      <Card>
        <CardContent className="space-y-5 p-6">
          <SectionHeading
            title="Backend connection"
            description={`Defaults to ${env.apiBaseUrl}.`}
          />
          <div className="space-y-2">
            <Label htmlFor="api-url">Base URL</Label>
            <div className="flex flex-wrap gap-2">
              <Input
                id="api-url"
                value={apiUrl}
                onChange={(event) => setApiUrl(event.target.value)}
                placeholder={env.apiBaseUrl}
                spellCheck={false}
                autoComplete="off"
                className="min-w-56 flex-1 font-mono text-xs"
              />
              <Button onClick={() => void saveApiUrl()}>
                <Check className="size-4" />
                Save
              </Button>
              <Button
                variant="outline"
                onClick={() => void testConnection()}
                disabled={testing}
              >
                <Plug className="size-4" />
                {testing ? "Testing…" : "Test"}
              </Button>
            </div>
            <p className="text-muted-foreground text-xs">
              Leave empty to fall back to the build-time value.
            </p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-6">
          <SectionHeading
            title="Appearance"
            description="CodeAtlas is designed for dark rooms and long sessions."
          />
          <div className="divide-border/70 mt-1 divide-y">
            <SettingRow
              label="Theme"
              description="Warm dark is the default."
              control={
                <Select
                  value={theme}
                  onValueChange={(value) => setTheme(value as Theme)}
                >
                  <SelectTrigger aria-label="Theme">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="dark">Dark</SelectItem>
                    <SelectItem value="light">Light</SelectItem>
                    <SelectItem value="system">System</SelectItem>
                  </SelectContent>
                </Select>
              }
            />
            <SettingRow
              label="Referenced files panel"
              description="Show the files each answer cited, beside the conversation."
              htmlFor="show-referenced"
              control={
                <Switch
                  id="show-referenced"
                  checked={preferences.showReferencedFiles}
                  onCheckedChange={(checked) =>
                    update("showReferencedFiles", checked)
                  }
                />
              }
            />
            <SettingRow
              label="Reduce motion"
              description="Your system preference is always respected; this forces it on."
              htmlFor="reduce-motion"
              control={
                <Switch
                  id="reduce-motion"
                  checked={preferences.reduceMotion}
                  onCheckedChange={(checked) => update("reduceMotion", checked)}
                />
              }
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-6">
          <SectionHeading
            title="Answer defaults"
            description="Applied to every question you ask."
          />
          <div className="divide-border/70 mt-1 divide-y">
            <SettingRow
              label="Retrieved chunks"
              description="How many pieces of code to pull in before answering (top_k)."
              htmlFor="top-k"
              control={
                <Input
                  id="top-k"
                  type="number"
                  min={1}
                  max={50}
                  value={preferences.topK}
                  onChange={(event) =>
                    update(
                      "topK",
                      Math.min(Math.max(Number(event.target.value) || 1, 1), 50),
                    )
                  }
                />
              }
            />
            <SettingRow
              label="Context budget"
              description="Maximum tokens of code sent to the model."
              htmlFor="max-tokens"
              control={
                <Input
                  id="max-tokens"
                  type="number"
                  min={100}
                  step={500}
                  value={preferences.maxContextTokens}
                  onChange={(event) =>
                    update(
                      "maxContextTokens",
                      Math.max(Number(event.target.value) || 100, 100),
                    )
                  }
                />
              }
            />
            <SettingRow
              label="Temperature"
              description="Lower keeps answers closer to the code. 0.2 is a good default."
              htmlFor="temperature"
              control={
                <Input
                  id="temperature"
                  type="number"
                  min={0}
                  max={2}
                  step={0.1}
                  value={preferences.temperature}
                  onChange={(event) =>
                    update(
                      "temperature",
                      Math.min(Math.max(Number(event.target.value) || 0, 0), 2),
                    )
                  }
                />
              }
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="space-y-4 p-6">
          <SectionHeading
            title="Local data"
            description="Repository history lives in this browser, never on the server."
            actions={
              <Badge variant="muted">
                {repositories.length} tracked
              </Badge>
            }
          />
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              onClick={() => {
                reset();
                toast.success("Preferences reset to defaults.");
              }}
            >
              <RotateCcw className="size-4" />
              Reset preferences
            </Button>
            <Button
              variant="outline"
              onClick={() => setClearOpen(true)}
              disabled={repositories.length === 0}
            >
              <Trash2 className="size-4" />
              Clear repository history
            </Button>
          </div>
        </CardContent>
      </Card>

      <ConfirmDialog
        open={clearOpen}
        onOpenChange={setClearOpen}
        title="Clear repository history?"
        description="This forgets every repository in this browser. Indexed vectors stay in Qdrant and can be used again after re-adding the path."
        confirmLabel="Clear history"
        destructive
        onConfirm={() => {
          clear();
          setClearOpen(false);
          toast.success("Repository history cleared.");
        }}
      />
    </PageContainer>
  );
}
