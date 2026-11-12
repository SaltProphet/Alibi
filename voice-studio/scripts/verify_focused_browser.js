/* Run through playwright-cli run-code --filename against the isolated test server. */
async (page) => {
  if (!['8875', '8765'].includes(new URL(page.url()).port)) {
    throw Error('Use the isolated test server on port 8875 or the local server on port 8765.');
  }
  await page.reload();
  await page.setViewportSize({width: 1041, height: 700});
  await page.getByRole('button', {name: 'Generate', exact: true}).waitFor();
  if (await page.getByRole('button', {name: 'Visual', exact: true}).count()) {
    throw Error('Visual mode is still exposed in the shipped navigation.');
  }
  if (await page.locator('iframe, canvas').count()) {
    throw Error('Standard view mounted an archived visual surface.');
  }
  const views = ['Voices', 'Generate', 'Record & Edit', 'Transcribe', 'Arrange', 'Video'];
  for (const name of views) {
    await page.getByRole('button', {name, exact: true}).click();
    await page.getByRole('main').waitFor();
  }
  await page.setViewportSize({width: 430, height: 900});
  const mobile = await page.evaluate(() => ({width: innerWidth, documentWidth: document.documentElement.scrollWidth}));
  if (mobile.documentWidth > mobile.width) throw Error('Mobile document overflows horizontally.');
  return {views, mobile};
};
