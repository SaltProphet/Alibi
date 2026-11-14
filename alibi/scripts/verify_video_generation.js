async page => {
 await page.getByLabel('Video narration text',{exact:true}).fill('Welcome to the video studio.');
 await page.getByLabel('Video saved voice',{exact:true}).selectOption('8080860b277842f9a7d09ba6084509b1');
 await page.getByRole('button',{name:'Generate & place narration',exact:true}).click();
 await page.getByRole('button',{name:'Remove narration 1',exact:true}).waitFor({timeout:180000});
 await page.getByRole('button',{name:'Export narrated MP4',exact:true}).click();
 await page.getByRole('link',{name:'Download narrated MP4',exact:true}).waitFor({timeout:120000});
 const result=page.getByLabel('Rendered narration preview',{exact:true});
 await result.evaluate(v=>new Promise((resolve,reject)=>{if(v.readyState>=2)return resolve();v.addEventListener('loadeddata',resolve,{once:true});v.addEventListener('error',reject,{once:true})}));
 await result.evaluate(v=>v.play());await page.waitForTimeout(1000);const meta=await result.evaluate(v=>({duration:v.duration,width:v.videoWidth,height:v.videoHeight,currentTime:v.currentTime,paused:v.paused,src:v.currentSrc}));await result.evaluate(v=>v.pause());
 if(meta.currentTime<.5||meta.duration<11.9)throw Error('Rendered playback failed '+JSON.stringify(meta));
 const href=await page.getByRole('link',{name:'Download narrated MP4',exact:true}).getAttribute('href');
 await page.reload();await page.getByRole('button',{name:'Video',exact:true}).click();await page.getByRole('button',{name:'Remove narration 1',exact:true}).waitFor();
 if(await page.getByLabel('Video narration text',{exact:true}).inputValue()!=='Welcome to the video studio.')throw Error('Project script not restored');
 return {pass:true,meta,href,restored:true};
}
