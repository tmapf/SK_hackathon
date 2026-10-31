import { expect, test } from "@playwright/test";

test.describe("public portal smoke", () => {
  test("loads bilingual shell and filters", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: /Warsaw Property Ideas/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /Wynajem|Rent/i })).toBeVisible();
    await page.getByRole("button", { name: "EN" }).click();
    await expect(page.getByText(/Browse municipal properties/i)).toBeVisible();
    await page.getByRole("button", { name: "PL" }).click();
    await expect(page.getByPlaceholder(/Ulica|Street/i)).toBeVisible();
  });

  test("admin login page is reachable", async ({ page }) => {
    await page.goto("/admin/login");
    await expect(page.getByRole("heading", { name: /Admin login/i })).toBeVisible();
    await expect(page.getByLabel(/Username/i)).toBeVisible();
  });
});
