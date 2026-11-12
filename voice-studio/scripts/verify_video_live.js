async page => {
 await page.goto('http://127.0.0.1:8875');await page.getByRole('button',{name:'Video',exact:true}).click();await page.getByLabel('Open video project',{exact:true}).selectOption('836e2815e64c4374b6ac1ecea4fe44ae');
 await page.getByRole('button',{name:'Export narrated MP4',exact:true}).click();await page.getByRole('link',{name:'Download narrated MP4',exact:true}).waitFor({timeout:120000});
 const [download]=await Promise.all([page.waitForEvent('download'),page.getByRole('link',{name:'Download narrated MP4',exact:true}).click()]);
 if(await download.failure())throw Error(await download.failure());
 await download.saveAs('work/video-narration-demo.mp4');
 const name=download.suggestedFilename();
 await page.goto('http://127.0.0.1:8765');await page.getByRole('button',{name:'Video',exact:true}).click();await page.getByRole('heading',{name:'Video narration',exact:true}).waitFor();
 const endpoints=await page.evaluate(async()=>{const r=await fetch('/api/videos');return {status:r.status,projects:(await r.json()).length}});if(endpoints.status!==200)throw Error('Live videos endpoint unavailable');
 return {downloaded:true,name,liveApp:'http://127.0.0.1:8765',videoWorkspaceVisible:true,endpoints};
}
