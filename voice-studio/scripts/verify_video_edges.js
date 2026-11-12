async page => {
 const result={};
 await page.getByRole('button',{name:'Play range with narration',exact:true}).click();await page.waitForTimeout(1000);
 result.preview=await page.getByLabel('Source video preview',{exact:true}).evaluate(v=>({currentTime:v.currentTime,paused:v.paused}));if(result.preview.currentTime<2.5)throw Error('Narrated range preview did not run');
 await page.getByRole('button',{name:'Record & edit',exact:true}).click();result.pausedOnExit=await page.locator('video').first().evaluate(v=>v.paused);if(!result.pausedOnExit)throw Error('Video playing after exit');
 await page.getByRole('button',{name:'Video',exact:true}).click();
 await page.getByLabel('Video range start',{exact:true}).fill('11');await page.getByLabel('Video range end',{exact:true}).fill('10');if(await page.getByRole('button',{name:'Generate & place narration',exact:true}).isEnabled())throw Error('Invalid range accepted');
 await page.getByLabel('Video range start',{exact:true}).fill('2');await page.getByLabel('Video range end',{exact:true}).fill('2.5');
 await page.getByRole('button',{name:'Generate & place narration',exact:true}).click();await page.getByRole('button',{name:'Place saved take in current range',exact:true}).waitFor({timeout:180000});
 result.overlongTakeRetained=true;await page.getByLabel('Video range start',{exact:true}).fill('6');await page.getByLabel('Video range end',{exact:true}).fill('10');await page.getByRole('button',{name:'Place saved take in current range',exact:true}).click();await page.getByRole('button',{name:'Remove narration 2',exact:true}).waitFor();
 await page.getByRole('button',{name:'Remove narration 2',exact:true}).click();await page.waitForFunction(()=>!document.querySelector('[aria-label="Video range start"]').disabled);
 await page.getByLabel('Import video',{exact:true}).setInputFiles('work/video-fixture.webm');await page.waitForFunction(()=>{const v=document.querySelector('[aria-label="Open video project"]');return v.selectedOptions[0].textContent.endsWith('.webm')});
 await page.waitForFunction(()=>{const v=document.querySelector('[aria-label="Source video preview"]');return v.readyState>=2});
 result.webm=await page.getByLabel('Source video preview',{exact:true}).evaluate(v=>({duration:v.duration,width:v.videoWidth}));
 await page.setViewportSize({width:390,height:844});result.mobile=await page.evaluate(()=>({body:document.body.scrollWidth,viewport:innerWidth}));if(result.mobile.body>result.mobile.viewport+1)throw Error('Mobile overflow '+JSON.stringify(result.mobile));
 await page.screenshot({path:'work/video-mobile.png',fullPage:true});await page.setViewportSize({width:1280,height:900});
 return result;
}
