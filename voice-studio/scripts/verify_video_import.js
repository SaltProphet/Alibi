async page => {
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.getByRole('button',{name:'Video',exact:true}).click();
 await page.getByLabel('Import video',{exact:true}).setInputFiles('work/video-fixture.mp4');
 await page.getByLabel('Video range end',{exact:true}).waitFor();await page.waitForFunction(()=>!document.querySelector('[aria-label="Video range start"]').disabled);
 const video=page.getByLabel('Source video preview',{exact:true});
 await video.evaluate(v=>new Promise((resolve,reject)=>{if(v.readyState>=2)return resolve();v.addEventListener('loadeddata',resolve,{once:true});v.addEventListener('error',reject,{once:true})}));
 const meta=await video.evaluate(v=>({duration:v.duration,width:v.videoWidth,height:v.videoHeight}));
 if(meta.duration!==12||meta.width!==640)throw Error('Wrong browser video metadata '+JSON.stringify(meta));
 await page.getByLabel('Video range timeline',{exact:true}).scrollIntoViewIfNeeded();const timeline=await page.getByLabel('Video range timeline',{exact:true}).boundingBox();
 await page.mouse.move(timeline.x+timeline.width/6,timeline.y+15);await page.mouse.down();await page.mouse.move(timeline.x+timeline.width*5/6,timeline.y+15,{steps:12});await page.mouse.up();
 const start=Number(await page.getByLabel('Video range start',{exact:true}).inputValue()),end=Number(await page.getByLabel('Video range end',{exact:true}).inputValue());
 if(Math.abs(start-2)>.1||Math.abs(end-10)>.1)throw Error('Drag range wrong '+start+' '+end);
 await page.getByLabel('Video range start',{exact:true}).fill('2');await page.getByLabel('Video range end',{exact:true}).fill('10');
 await page.getByRole('button',{name:'Play range with narration',exact:true}).click();
 await page.waitForTimeout(1300);const current=await video.evaluate(v=>v.currentTime);if(current<=2.5)throw Error('Video did not play');
 await page.getByRole('button',{name:'Stop video',exact:true}).click();
 await page.getByRole('button',{name:'Save video project',exact:true}).click();
 await page.getByRole('button',{name:'Record & edit',exact:true}).click();await page.getByRole('button',{name:'Video',exact:true}).click();
 if(await page.getByLabel('Video range start',{exact:true}).inputValue()!=='2')throw Error('Navigation lost range');
 console.log(JSON.stringify({checkpoint:'import-preview-range',meta,dragRange:{start,end},playbackTime:current,errors}));
}
